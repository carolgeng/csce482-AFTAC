import os
import re
import requests
import wget
from tqdm import tqdm
import gzip
import json
import logging

from flask import Flask, jsonify
from database import db
from config import Config
from dotenv import load_dotenv

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

db.init_app(app)
migrate = Migrate(app, db)

from models import Paper, Author, Journal, Citation

# Set up logging
logging.basicConfig(level=logging.INFO)

API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
DATASET_NAME = "s2orc"
LOCAL_PATH = "/Users/alecklem/aftac"
os.makedirs(LOCAL_PATH, exist_ok=True)

def save_author_to_db(author_data):
    author_name = author_data['name']
    existing_author = Author.query.filter_by(name=author_name).first()
    if not existing_author:
        new_author = Author(name=author_name)
        db.session.add(new_author)
        db.session.commit()
        return new_author
    return existing_author

def save_paper_to_db(paper_data):
    try:
        title = paper_data.get('title', None)
        abstract = paper_data.get('abstract', None)
        year = paper_data.get('year', None)
        total_citations = len(paper_data.get('citations', []))

        existing_paper = Paper.query.filter_by(title=title).first()
        if not existing_paper:
            new_paper = Paper(
                title=title,
                abstract=abstract,
                publication_year=year,
                total_citations=total_citations
            )
            db.session.add(new_paper)

            if 'authors' in paper_data:
                for author in paper_data['authors']:
                    new_author = save_author_to_db(author)
                    paper_author = PaperAuthors(paper_id=new_paper.id, author_id=new_author.id)
                    db.session.add(paper_author)
            
            db.session.commit()  # Commit after processing everything

        else:
            logging.info(f"Paper '{title}' already exists.")

    except Exception as e:
        logging.error(f"Error saving paper: {e}")

def download_s2orc_dataset():
    response = requests.get("https://api.semanticscholar.org/datasets/v1/release/latest").json()
    RELEASE_ID = response["release_id"]
    logging.info(f"Latest release ID: {RELEASE_ID}")

    response = requests.get(f"https://api.semanticscholar.org/datasets/v1/release/{RELEASE_ID}/dataset/{DATASET_NAME}/", 
                            headers={"x-api-key": API_KEY}).json()

    for url in tqdm(response["files"]):
        match = re.match(r"https://ai2-s2ag.s3.amazonaws.com/staging/(.*)/s2orc/(.*).gz(.*)", url)
        SHARD_ID = match.group(2)
        file_path = os.path.join(LOCAL_PATH, f"{SHARD_ID}.gz")
        
        if not os.path.exists(file_path):
            logging.info(f"Downloading {SHARD_ID}...")
            wget.download(url, out=file_path)

            with gzip.open(file_path, 'rb') as f_in:
                for line in f_in:
                    paper_data = json.loads(line)
                    save_paper_to_db(paper_data)
        else:
            logging.info(f"File {file_path} already exists. Skipping download.")

    logging.info(f"Downloaded and processed shard {SHARD_ID}")

@app.route('/download-s2orc')
def download_and_store_s2orc():
    download_s2orc_dataset()
    return jsonify({"message": "S2ORC dataset download and storage process started!"})

if __name__ == '__main__':
    app.run(debug=True)
