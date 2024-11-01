# etl.py

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Paper, Author, Journal, Concept, PaperAuthor, PaperConcept
from config import DATABASE_URL
import datetime
import time
import logging
from dotenv import load_dotenv
import os
import sys
import traceback
import re

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("etl.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create the database engine
engine = create_engine(DATABASE_URL)
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

def test_database_connection():
    try:
        # Attempt to connect and perform a simple query
        session.execute('SELECT 1')
        logger.info("Database connection successful.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)

def extract_numeric_id(openalex_id):
    if not isinstance(openalex_id, str):
        return None
    match = re.search(r'/([A-Z]?[\d]+)$', openalex_id)
    return match.group(1) if match else None

def fetch_papers(concept_ids, per_page=200, batch_size=5000, cursor='*'):
    base_url = 'https://api.openalex.org/works'
    headers = {'User-Agent': 'AI_Driven_RD (alecklem@tamu.edu)'}  # Replace with your email
    concept_filter = '|'.join([f'C{cid}' for cid in concept_ids])
    params = {
        'filter': f'concepts.id:{concept_filter}',
        'per-page': per_page,
        'cursor': cursor,
        'sort': 'cited_by_count:desc'  # Optionally sort by citation count
    }
    papers = []
    total_results = 0
    while total_results < batch_size:
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            if response.status_code != 200:
                logger.error(f"Error fetching papers: {response.status_code}")
                break
            data = response.json()
            results = data.get('results', [])
            papers.extend(results)
            total_results += len(results)
            if total_results >= batch_size:
                break
            cursor = data.get('meta', {}).get('next_cursor')
            if not cursor:
                break
            params['cursor'] = cursor
            time.sleep(0.2)  # Respect API rate limits
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            break
    next_cursor = data.get('meta', {}).get('next_cursor')
    return papers, next_cursor

def process_papers(papers):
    logger.info(f"Inside process papers")
    total_papers_fetched = len(papers)
    papers_inserted = 0
    papers_skipped_missing_fields = 0
    papers_already_exists = 0

    # Fetch existing OpenAlex IDs to avoid duplicates
    paper_openalex_ids = [paper.get('id') for paper in papers if paper.get('id')]
    existing_papers = session.query(Paper).filter(Paper.openalex_id.in_(paper_openalex_ids)).all()
    existing_openalex_ids = set(paper.openalex_id for paper in existing_papers)

    # Collect all unique author and concept IDs
    author_openalex_ids = set()
    concept_openalex_ids = set()
    for paper_data in papers:
        if not paper_data or not isinstance(paper_data, dict):
            continue
        for author_data in paper_data.get('authorships', []):
            if not author_data or not isinstance(author_data, dict):
                continue
            author_info = author_data.get('author')
            if not author_info or not isinstance(author_info, dict):
                continue
            author_openalex_id = author_info.get('id')
            if author_openalex_id and isinstance(author_openalex_id, str):
                author_openalex_ids.add(author_openalex_id)
        for concept_data in paper_data.get('concepts', []):
            if not concept_data or not isinstance(concept_data, dict):
                continue
            concept_openalex_id = concept_data.get('id')
            if concept_openalex_id and isinstance(concept_openalex_id, str):
                concept_openalex_ids.add(concept_openalex_id)

    # Bulk fetch existing authors and concepts
    existing_authors = session.query(Author).filter(Author.openalex_id.in_(author_openalex_ids)).all()
    existing_authors_dict = {author.openalex_id: author for author in existing_authors}

    existing_concepts = session.query(Concept).filter(Concept.openalex_id.in_(concept_openalex_ids)).all()
    existing_concepts_dict = {concept.openalex_id: concept for concept in existing_concepts}

    # Sets to track known OpenAlex IDs
    all_author_openalex_ids = set(existing_authors_dict.keys())
    all_concept_openalex_ids = set(existing_concepts_dict.keys())
    new_authors = {}
    new_concepts = {}
    new_journals = {}
    existing_paper_author_pairs = set()
    existing_paper_concept_pairs = set()
    new_paper_openalex_ids = set()

    papers_in_batch = 0

    for idx, paper_data in enumerate(papers, start=1):
        try:
            if idx % 100 == 0:
                logger.info(f"Processing paper {idx}/{total_papers_fetched}")

            if not paper_data or not isinstance(paper_data, dict):
                continue

            openalex_id = paper_data.get('id')
            if not openalex_id or not isinstance(openalex_id, str):
                logger.error(f"Invalid openalex_id at index {idx}: {openalex_id}")
                continue
            if openalex_id in existing_openalex_ids or openalex_id in new_paper_openalex_ids:
                papers_already_exists += 1
                continue

            new_paper_openalex_ids.add(openalex_id)

            doi = paper_data.get('doi')
            title = paper_data.get('title')
            abstract_inverted_index = paper_data.get('abstract_inverted_index')

            if not title or not abstract_inverted_index:
                papers_skipped_missing_fields += 1
                continue

            # Reconstruct abstract
            try:
                if isinstance(abstract_inverted_index, dict):
                    all_positions = [pos for positions in abstract_inverted_index.values() for pos in positions]
                    if all_positions:
                        max_position = max(all_positions)
                        abstract_words = [None] * (max_position + 1)
                        for word, positions in abstract_inverted_index.items():
                            for pos in positions:
                                abstract_words[pos] = word
                        abstract = ' '.join(filter(None, abstract_words))
                    else:
                        abstract = ''
                else:
                    abstract = ''
            except Exception as e:
                logger.error(f"Error reconstructing abstract for paper at index {idx}: {e}")
                logger.error(traceback.format_exc())
                abstract = ''

            publication_date = paper_data.get('publication_date')
            publication_year = None
            if publication_date:
                try:
                    publication_year = datetime.datetime.strptime(publication_date, '%Y-%m-%d').year
                except ValueError:
                    pass

            total_citations = paper_data.get('cited_by_count', 0)
            influential_citations = len(paper_data.get('referenced_works', []))
            pdf_url = paper_data.get('primary_location', {}).get('pdf_url')

            # Process Journal
            journal_data = paper_data.get('host_venue', {})
            journal_name = None
            if journal_data and isinstance(journal_data, dict):
                journal_name = journal_data.get('display_name')
            journal = None
            if journal_name:
                if journal_name in new_journals:
                    journal = new_journals[journal_name]
                else:
                    journal = session.query(Journal).filter_by(journal_name=journal_name).first()
                    if not journal:
                        journal = Journal(journal_name=journal_name)
                        session.add(journal)
                    new_journals[journal_name] = journal

            # Create Paper instance
            paper = Paper(
                openalex_id=openalex_id,
                title=title,
                abstract=abstract,
                publication_year=publication_year,
                journal=journal,
                total_citations=total_citations,
                pdf_url=pdf_url,
                doi=doi,
                influential_citations=influential_citations
            )
            session.add(paper)
            papers_inserted += 1
            papers_in_batch += 1

            # Process Authors
            authorships = paper_data.get('authorships', [])
            for author_data in authorships:
                try:
                    if not author_data or not isinstance(author_data, dict) or 'author' not in author_data:
                        continue
                    author_info = author_data.get('author')
                    if not author_info or not isinstance(author_info, dict):
                        continue
                    author_name = author_info.get('display_name')
                    author_openalex_id = author_info.get('id')
                    if not author_name or not author_openalex_id or not isinstance(author_openalex_id, str):
                        continue
                    if author_openalex_id in all_author_openalex_ids:
                        if author_openalex_id in existing_authors_dict:
                            author = existing_authors_dict[author_openalex_id]
                        else:
                            author = new_authors[author_openalex_id]
                    else:
                        author = Author(name=author_name, openalex_id=author_openalex_id)
                        session.add(author)
                        new_authors[author_openalex_id] = author
                        all_author_openalex_ids.add(author_openalex_id)

                    # Create PaperAuthor association
                    paper_author_key = (paper.openalex_id, author.openalex_id)
                    if paper_author_key in existing_paper_author_pairs:
                        continue
                    existing_paper_author_pairs.add(paper_author_key)

                    paper_author = PaperAuthor(paper=paper, author=author)
                    session.add(paper_author)
                except Exception as e:
                    logger.error(f"Error processing author in paper at index {idx}: {e}")
                    logger.error(f"Author data: {author_data}")
                    logger.error(traceback.format_exc())
                    continue  # Skip to next author

            # Process Concepts
            concepts = paper_data.get('concepts', [])
            for concept_data in concepts:
                try:
                    if not concept_data or not isinstance(concept_data, dict):
                        continue
                    concept_name = concept_data.get('display_name')
                    concept_openalex_id = concept_data.get('id')
                    concept_score = concept_data.get('score', 0)
                    if not concept_name or not concept_openalex_id or not isinstance(concept_openalex_id, str):
                        continue
                    if concept_openalex_id in all_concept_openalex_ids:
                        if concept_openalex_id in existing_concepts_dict:
                            concept = existing_concepts_dict[concept_openalex_id]
                        else:
                            concept = new_concepts[concept_openalex_id]
                    else:
                        concept = Concept(name=concept_name, openalex_id=concept_openalex_id)
                        session.add(concept)
                        new_concepts[concept_openalex_id] = concept
                        all_concept_openalex_ids.add(concept_openalex_id)

                    # Create PaperConcept association
                    paper_concept_key = (paper.openalex_id, concept.openalex_id)
                    if paper_concept_key in existing_paper_concept_pairs:
                        continue
                    existing_paper_concept_pairs.add(paper_concept_key)

                    paper_concept = PaperConcept(paper=paper, concept=concept, score=concept_score)
                    session.add(paper_concept)
                except Exception as e:
                    logger.error(f"Error processing concept in paper at index {idx}: {e}")
                    logger.error(f"Concept data: {concept_data}")
                    logger.error(traceback.format_exc())
                    continue  # Skip to next concept

            # Periodic commit every 500 papers
            if idx % 500 == 0:
                try:
                    session.commit()
                    # Clear caches
                    new_authors.clear()
                    new_concepts.clear()
                    new_journals.clear()
                    existing_paper_author_pairs.clear()
                    existing_paper_concept_pairs.clear()
                    papers_in_batch = 0
                    logger.info(f"Committed up to paper {idx}")
                except Exception as e:
                    logger.error(f"Error during batch commit at index {idx}: {e}")
                    logger.error(traceback.format_exc())
                    session.rollback()
                    # Adjust counts
                    papers_inserted -= papers_in_batch
                    # Remove uncommitted objects from session
                    session.expunge_all()
                    continue

        except Exception as e:
            logger.error(f"Error processing paper at index {idx}: {e}")
            logger.error(traceback.format_exc())
            session.rollback()
            # Adjust counts
            papers_inserted -= papers_in_batch
            papers_in_batch = 0
            continue

    # Final commit
    try:
        session.commit()
    except Exception as e:
        logger.error(f"Error during final commit: {e}")
        logger.error(traceback.format_exc())
        session.rollback()
        # Adjust counts
        papers_inserted -= papers_in_batch

    logger.info("Finished processing papers")
    logger.info(f"Papers inserted: {papers_inserted}")
    logger.info(f"Papers skipped (missing fields): {papers_skipped_missing_fields}")
    logger.info(f"Papers already existed: {papers_already_exists}")

def fetch_and_process_citations(paper_data, session):
    cited_works = paper_data.get('referenced_works', [])
    paper_id = get_paper_id_by_openalex(paper_data['id'], session)
    if not paper_id:
        return
    for cited_openalex_id in cited_works:
        citing_paper_id = get_paper_id_by_openalex(cited_openalex_id, session)
        if citing_paper_id:
            citation = Citation(paper_id=paper_id, citing_paper_id=citing_paper_id)
            session.add(citation)

def get_paper_id_by_openalex(openalex_id, session):
    """Helper function to retrieve the internal ID of a paper based on OpenAlex ID"""
    paper = session.query(Paper).filter_by(openalex_id=openalex_id).first()
    return paper.id if paper else None


def main():
    test_database_connection()
    concept_ids = ['154945302', '119857082']  # Example concept IDs

    per_page = 200  # Max per-page limit for OpenAlex API
    batch_size = 5000  # Number of papers to fetch in each batch
    cursor = '*'  # Initial cursor

    try:
        while True:
            logger.info("Starting to fetch papers...")
            papers, next_cursor = fetch_papers(concept_ids, per_page=per_page, batch_size=batch_size, cursor=cursor)
            if not papers:
                logger.info("No more papers to fetch. Exiting loop.")
                break
            logger.info(f"Fetched {len(papers)} papers in total.")
            
            # Process papers and their citations
            process_papers(papers)
            
            if not next_cursor or next_cursor == cursor:
                logger.info("No new cursor returned or cursor hasn't changed. Exiting loop.")
                break
            cursor = next_cursor
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Stopping the script.")
    finally:
        session.close()

if __name__ == '__main__':
    main()
