# app.py
import os
import re
import requests
import wget
from tqdm import tqdm
import gzip
import json
import logging
from datetime import datetime

from flask import Flask, jsonify
from dotenv import load_dotenv

from src.data_extraction.database import db
from flask_migrate import Migrate

load_dotenv()
app = Flask(__name__)

# Explicitly set the DATABASE_URL
database_url = os.environ.get('DATABASE_URL')

# Ensure proper format of the DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the db with the Flask app
db.init_app(app)
migrate = Migrate(app, db)

# Import models after initializing db
from src.data_extraction.models import Paper, Author, Journal, paper_authors


# Set up logging
logging.basicConfig(level=logging.INFO)

DATASET_NAME = "s2orc"
API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

LOCAL_PATH = os.getcwd()
os.makedirs(LOCAL_PATH, exist_ok=True)

# Initialize counters
papers_saved = 0
papers_skipped = 0
total_papers_processed = 0


def normalize_text(text):
    # Remove special characters and extra whitespace
    text = re.sub(r'\W+', ' ', text)
    return text.strip().lower()

def is_relevant_paper(title, abstract):
    keywords = [
        'machine learning', 'artificial intelligence', 'deep learning', 'neural network',
        'data mining', 'natural language processing', 'computer vision',
        'reinforcement learning', 'supervised learning', 'unsupervised learning',
        'classification', 'regression', 'clustering', 'support vector machine',
        'random forest', 'decision tree', 'convolutional neural network', 'cnn', 'rnn',
        'recurrent neural network', 'transformer', 'bert', 'gpt', 'algorithm', 'model',
        'predictive analytics', 'pattern recognition', 'data science', 'k-means',
        'svm', 'naive bayes', 'bayesian network', 'ensemble learning', 'gradient boosting',
        'xgboost', 'lstm', 'long short-term memory', 'autoencoder', 'generative adversarial network',
        'gan', 'k-nearest neighbors', 'knn', 'artificial neural network', 'perceptron',
        'dropout', 'batch normalization', 'hyperparameter tuning', 'feature extraction',
        'feature selection', 'dimensionality reduction', 'pca', 'principal component analysis',
        'tsne', 'stochastic gradient descent', 'sgd', 'backpropagation', 'loss function',
        'activation function', 'cross-validation', 'overfitting', 'underfitting', 'bias-variance tradeoff'
    ]

    content = ''
    if title: 
        content += normalize_text(title)
    if abstract: 
        content += ' ' + normalize_text(abstract)

    # Combine keywords into a regex pattern
    pattern = r'\b(' + '|'.join(map(re.escape, keywords)) + r')\b'
    return re.search(pattern, content) is not None

def save_paper_to_db(paper_data):
    global total_papers_processed, papers_saved, papers_skipped
    total_papers_processed += 1

    try:
        logging.info(f"Paper data keys: {paper_data.keys()}")

        content = paper_data.get('content', None)
        if content:
            logging.info("'content' is already a dictionary.")
            logging.info(f"Content keys: {content.keys()}")

            text = content.get('text', "")
            if not isinstance(text, str):
                logging.error(f"Unexpected type for text: {type(text)}")
                text = ""
            annotations = content.get('annotations', {})

            logging.info(f"Annotations type: {type(annotations)}")
            logging.info(f"Annotations keys: {list(annotations.keys())}")

            title = None
            abstract = None
            year = None

            # Initialize title_annotations and abstract_annotations
            title_annotations = []
            abstract_annotations = []

            # Process title
            title_annotations_data = annotations.get('title')
            if title_annotations_data:
                if isinstance(title_annotations_data, str):
                    try:
                        title_annotations = json.loads(title_annotations_data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Error parsing title annotations: {e}")
                elif isinstance(title_annotations_data, list):
                    title_annotations = title_annotations_data
                else:
                    logging.error(f"Unexpected type for title annotations: {type(title_annotations_data)}")

                if title_annotations:
                    ann = title_annotations[0]
                    start = ann.get('start')
                    end = ann.get('end')
                    try:
                        start = int(start)
                        end = int(end)
                        title = text[start:end].strip()
                    except (ValueError, TypeError) as e:
                        logging.error(f"Invalid indices in title annotation: {ann} | Error: {e}")
            else:
                logging.error("Title annotations are missing or None.")

            # Process abstract
            abstract_annotations_data = annotations.get('abstract')
            if abstract_annotations_data:
                if isinstance(abstract_annotations_data, str):
                    try:
                        abstract_annotations = json.loads(abstract_annotations_data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Error parsing abstract annotations: {e}")
                elif isinstance(abstract_annotations_data, list):
                    abstract_annotations = abstract_annotations_data
                else:
                    logging.error(f"Unexpected type for abstract annotations: {type(abstract_annotations_data)}")

                if abstract_annotations:
                    ann = abstract_annotations[0]
                    start = ann.get('start')
                    end = ann.get('end')
                    try:
                        start = int(start)
                        end = int(end)
                        abstract = text[start:end].strip()
                        # Truncate if necessary
                        max_abstract_length = 1000
                        if len(abstract) > max_abstract_length:
                            logging.warning(f"Abstract for paper '{title}' is unusually long. Truncating.")
                            abstract = abstract[:max_abstract_length] + '...'
                    except (ValueError, TypeError) as e:
                        logging.error(f"Invalid indices in abstract annotation: {ann} | Error: {e}")
            else:
                logging.error("Abstract annotations are missing or None.")

            # Log extracted title and abstract
            logging.info(f"Extracted title: {title}")
            logging.info(f"Extracted abstract: {abstract}")

            # Extract publication year
            year = extract_publication_year(text, annotations)

            # Check if paper is relevant
            if not is_relevant_paper(title, abstract):
                logging.info(f"Paper '{title}' is not relevant to ML/AI. Skipping.")
                papers_skipped += 1
                return

            # Process authors
            authors_list = []
            author_annotations_data = annotations.get('author')
            if author_annotations_data:
                if isinstance(author_annotations_data, str):
                    try:
                        author_annotations = json.loads(author_annotations_data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Error parsing author annotations: {e}")
                        author_annotations = []
                elif isinstance(author_annotations_data, list):
                    author_annotations = author_annotations_data
                else:
                    logging.error(f"Unexpected type for author annotations: {type(author_annotations_data)}")
                    author_annotations = []

                for ann in author_annotations:
                    start = ann.get('start')
                    end = ann.get('end')
                    try:
                        start = int(start)
                        end = int(end)
                        author_name = text[start:end].strip()
                        if author_name:
                            authors_list.append(author_name)
                    except (ValueError, TypeError) as e:
                        logging.error(f"Invalid indices in author annotation: {ann} | Error: {e}")
            else:
                logging.error("Author annotations are missing or None.")

            # Save the paper
            existing_paper = Paper.query.filter_by(title=title).first()
            if not existing_paper:
                new_paper = Paper(
                    title=title,
                    abstract=abstract,
                    publication_year=year,
                    raw_content=text  # Store raw text
                    # Add other fields as necessary
                )
                db.session.add(new_paper)
                db.session.commit()
                papers_saved += 1

                # Save authors
                for author_name in authors_list:
                    existing_author = Author.query.filter_by(name=author_name).first()
                    if not existing_author:
                        new_author = Author(name=author_name)
                        db.session.add(new_author)
                        db.session.commit()
                    else:
                        new_author = existing_author
                    new_paper.authors.append(new_author)
                db.session.commit()
            else:
                logging.info(f"Paper '{title}' already exists.")
                papers_skipped += 1

            # Log counts every 100 papers
            if total_papers_processed % 100 == 0:
                logging.info(f"Processed: {total_papers_processed}, Saved: {papers_saved}, Skipped: {papers_skipped}")
        else:
            logging.error("'content' is missing or None.")
            papers_skipped += 1
    except Exception as e:
        logging.error(f"Error saving paper: {e}")
        db.session.rollback()
        papers_skipped += 1

def extract_publication_year(text, annotations):
    year = None
    current_year = datetime.now().year
    year_pattern = re.compile(r'\b(19|20)\d{2}\b')

    # Attempt to extract year from 'source' field
    source = annotations.get('source', '')
    if isinstance(source, str):
        match = year_pattern.search(source)
        if match:
            year_candidate = int(match.group())
            if 1900 <= year_candidate <= current_year:
                year = year_candidate
                logging.info(f"Extracted year from source: {year}")
    elif isinstance(source, dict):
        source_str = json.dumps(source)
        match = year_pattern.search(source_str)
        if match:
            year_candidate = int(match.group())
            if 1900 <= year_candidate <= current_year:
                year = year_candidate
                logging.info(f"Extracted year from source dict: {year}")

    # If year not found, attempt to extract from 'bibentry'
    if not year:
        bibentry_annotations_data = annotations.get('bibentry')
        bib_years = []
        if bibentry_annotations_data:
            if isinstance(bibentry_annotations_data, str):
                try:
                    bibentry_annotations = json.loads(bibentry_annotations_data)
                except json.JSONDecodeError as e:
                    logging.error(f"Error parsing bibentry annotations: {e}")
                    bibentry_annotations = []
            elif isinstance(bibentry_annotations_data, list):
                bibentry_annotations = bibentry_annotations_data
            else:
                logging.error(f"Unexpected type for bibentry annotations: {type(bibentry_annotations_data)}")
                bibentry_annotations = []

            for bib_entry in bibentry_annotations:
                start = bib_entry.get('start')
                end = bib_entry.get('end')
                try:
                    start = int(start)
                    end = int(end)
                    bib_text = text[start:end].strip()
                    # Search for all years in bib_text
                    matches = year_pattern.findall(bib_text)
                    for match in matches:
                        year_candidate = int(match)
                        if 1900 <= year_candidate <= current_year:
                            bib_years.append(year_candidate)
                except (ValueError, TypeError) as e:
                    logging.error(f"Invalid indices in bibentry annotation: {bib_entry} | Error: {e}")

            if bib_years:
                year = max(bib_years)
                logging.info(f"Estimated publication year from bibentry: {year}")
            else:
                logging.warning("No valid years found in bibentry annotations.")
        else:
            logging.warning("Bibentry annotations are missing or None.")

    return year

def download_s2orc_dataset():
    response = requests.get("https://api.semanticscholar.org/datasets/v1/release/latest").json()
    RELEASE_ID = response["release_id"]
    logging.info(f"Latest release ID: {RELEASE_ID}")

    response = requests.get(
        f"https://api.semanticscholar.org/datasets/v1/release/{RELEASE_ID}/dataset/{DATASET_NAME}/", 
        headers={"x-api-key": API_KEY}
    ).json()

    for url in tqdm(response["files"]):
        match = re.match(r"https://ai2-s2ag.s3.amazonaws.com/staging/(.*)/s2orc/(.*).gz(.*)", url)
        SHARD_ID = match.group(2)
        file_path = os.path.join(LOCAL_PATH, f"{SHARD_ID}.gz")
        
        if not os.path.exists(file_path):
            logging.info(f"Downloading {SHARD_ID}...")
            wget.download(url, out=file_path)
        else:
            logging.info(f"File {file_path} already exists. Skipping download.")

        # Process the downloaded file
        logging.info(f"Processing file {file_path}...")
        with gzip.open(file_path, 'rb') as f_in:
            for line in f_in:
                paper_data = json.loads(line)
                save_paper_to_db(paper_data)

    logging.info(f"Downloaded and processed shard {SHARD_ID}")

    # Log final counts
    logging.info(f"Total papers processed: {total_papers_processed}")
    logging.info(f"Papers saved: {papers_saved}")
    logging.info(f"Papers skipped: {papers_skipped}")

@app.route('/download-s2orc')
def download_and_store_s2orc():
    download_s2orc_dataset()
    return jsonify({"message": "S2ORC dataset download and storage process started!"})

if __name__ == '__main__':
    app.run(debug=False, port=5001)
