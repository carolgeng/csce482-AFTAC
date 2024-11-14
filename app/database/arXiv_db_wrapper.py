import sys
import os

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.database.DatabaseManager import DatabaseManager
from app.APIs.arXiv.arXiv_wrapper import api_handler

def main():
    # Prompt the user for the query keyword
    query = input('Enter the query string to search arXiv: ')

    # Initialize the database manager and API handler
    manager = DatabaseManager("data.db")
    handler = api_handler()

    # Start querying
    print(f"Querying arXiv for: {query}...")
    results_generator = handler.query(query, None)

    processed_count = 0
    inserted_papers = 0

    # Process results iteratively
    for result in results_generator:
        processed_count += 1

        # Extract arXiv ID from result.entry_id
        arxiv_id_full = result.entry_id.split('/')[-1] if hasattr(result, 'entry_id') else None
        # Optionally remove version number from arXiv ID
        arxiv_id = arxiv_id_full.split('v')[0] if arxiv_id_full else None

        # Check if a paper with the same DOI already exists
        existing_paper = manager.get_paper_by_doi(result.doi)

        if not existing_paper:
            # Insert the paper into the database
            inserted_papers += 1
            print(f"Inserting paper {inserted_papers}: {result.title}")
            paper_id = manager.insert_paper(
                corpus_id=None,  # Replace with an actual corpus_id if available
                title=result.title,
                abstract=result.summary,
                publication_year=result.published.year if hasattr(result, 'published') and result.published else None,
                journal_id=None,  # Journal data insertion is optional for now
                total_citations=0,
                influential_citations=0,
                delta_citations=0,
                citations_per_year=0.0,
                rank_citations_per_year=None,
                pdf_url=result.pdf_url if hasattr(result, 'pdf_url') else None,
                doi=result.doi if hasattr(result, 'doi') else None
            )
        else:
            # Use the existing paper ID if found
            paper_id = existing_paper['id']

        # Process authors (insert or get existing authors and paper_authors associations)
        if hasattr(result, 'authors') and result.authors is not None:
            for author in result.authors:
                author_name = author.name if hasattr(author, 'name') else str(author)
                author_id = manager.get_or_create_author(
                    name=author_name,
                    first_publication_year=None,
                    author_age=None,
                    h_index=0,
                    delta_h_index=None,
                    adopters=0,
                    total_papers=0,
                    delta_total_papers=None,
                    recent_coauthors=None,
                    coauthor_pagerank=0.0,
                    total_citations=0
                )

                # Insert into paper_authors association table using insert_or_ignore_paper_author
                manager.insert_or_ignore_paper_author(
                    paper_id=paper_id,
                    author_id=author_id
                )

    # Print summary
    if processed_count == 0:
        print("No results found for the given query.")
    else:
        print(f"Processed {processed_count} results from arXiv. Inserted {inserted_papers} new papers into the database.")

    # Close the database connection
    manager.close_connection()

if __name__ == '__main__':
    main()
