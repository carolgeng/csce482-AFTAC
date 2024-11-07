import sys
import os
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.database.DatabaseManager import DatabaseManager
from app.APIs.arXiv.arXiv_wrapper import api_handler

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Fetch papers from arXiv and store them in the database.')
    parser.add_argument('query', type=str, help='The query string to search arXiv.')
    args = parser.parse_args()

    logging.info(f"Starting script with query: {args.query}")

    # Initialize the database manager and API handler
    manager = DatabaseManager("data.db")
    handler = api_handler()

    # Use the query passed from the command line
    logging.info("Querying the arXiv API...")
    results = list(handler.query(args.query, None))

    if not results:
        logging.info("No results found for the query.")
        return

    logging.info(f"Found {len(results)} results. Processing them...")

    for idx, result in enumerate(results, start=1):
        logging.info(f"Processing result {idx}/{len(results)}: {result.title}")

        # Extract arXiv ID from result.entry_id
        arxiv_id_full = result.entry_id.split('/')[-1] if hasattr(result, 'entry_id') else None
        # Optionally remove version number from arXiv ID
        arxiv_id = arxiv_id_full.split('v')[0] if arxiv_id_full else None

        # Get or create journal
        journal_name = getattr(result, 'journal_ref', None)
        if journal_name:
            journal_id = manager.get_or_create_journal(
                journal_name=journal_name,
                mean_citations_per_paper=0.0,
                journal_h_index=0,
                total_papers_published=0
            )
            logging.info(f"Journal '{journal_name}' inserted/exists with ID {journal_id}.")
        else:
            journal_id = None  # Handle cases where journal_ref is None
            logging.info("No journal reference found for this paper.")

        # Insert paper and get paper_id
        paper_id = manager.insert_paper(
            corpus_id=None,  # Replace with actual corpus_id if available
            title=result.title,
            abstract=result.summary,
            publication_year=result.published.year if hasattr(result, 'published') and result.published else None,
            journal_id=journal_id,
            total_citations=0,
            influential_citations=0,
            delta_citations=0,
            citations_per_year=0.0,
            rank_citations_per_year=None,
            pdf_url=result.pdf_url if hasattr(result, 'pdf_url') else None,
            doi=result.doi if hasattr(result, 'doi') else None
        )
        logging.info(f"Paper '{result.title}' inserted with ID {paper_id}.")

        # Insert paper external IDs
        manager.insert_paper_external_id(
            paper_id=paper_id,
            arxiv_id=arxiv_id,
            doi=result.doi
        )
        logging.info(f"Paper external IDs inserted for paper ID {paper_id}.")

        # Process authors
        if hasattr(result, 'authors'):
            for author in result.authors:
                # Get or create author
                author_name = author.name if hasattr(author, 'name') else str(author)
                author_id = manager.get_or_create_author(
                    name=author_name,
                    h_index=0,
                    adopters=0,
                    total_papers=0,
                    coauthor_pagerank=0.0,
                    total_citations=0
                )
                logging.info(f"Author '{author_name}' inserted/exists with ID {author_id}.")

                # Insert into paper_authors association table
                manager.insert_paper_author(
                    paper_id=paper_id,
                    author_id=author_id
                )
                logging.info(f"Association between paper ID {paper_id} and author ID {author_id} inserted.")
        else:
            logging.info("No authors found for this paper.")

    # Close the database connection
    manager.close_connection()
    logging.info("Script completed successfully.")

if __name__ == '__main__':
    main()
