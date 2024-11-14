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
    print("Initializing database manager and API handler...")
    manager = DatabaseManager("data.db")
    handler = api_handler()

    # Use the query passed from the command line
    print(f"Querying arXiv with: {query}")
    results = list(handler.query(query, None))

    if not results:
        print("No results found for the given query.")
        return

    print(f"Found {len(results)} results. Processing them...")
    for idx, result in enumerate(results, start=1):
        print(f"Processing result {idx}/{len(results)}: {result.title}")
        
        # Extract arXiv ID from result.entry_id
        arxiv_id_full = result.entry_id.split('/')[-1] if hasattr(result, 'entry_id') else None
        # Optionally remove version number from arXiv ID
        arxiv_id = arxiv_id_full.split('v')[0] if arxiv_id_full else None

        # Get or create journal
        journal_name = getattr(result, 'journal_ref', None)
        if journal_name:
            print(f"Getting or creating journal: {journal_name}")
            journal_id = manager.get_or_create_journal(
                journal_name=journal_name,
                mean_citations_per_paper=0.0,
                delta_mean_citations_per_paper=None,
                journal_h_index=0,
                delta_journal_h_index=None,
                max_citations_paper=None,
                total_papers_published=0,
                delta_total_papers_published=None
            )
        else:
            journal_id = None  # Handle cases where journal_ref is None
            print("No journal reference found for this paper.")

        # Insert paper and get paper_id
        print(f"Inserting paper: {result.title}")
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

        # Process authors
        if hasattr(result, 'authors'):
            for author in result.authors:
                author_name = author.name if hasattr(author, 'name') else str(author)
                print(f"Getting or creating author: {author_name}")
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

                # Insert into paper_authors association table
                print(f"Inserting association between paper ID {paper_id} and author ID {author_id}")
                manager.insert_paper_author(
                    paper_id=paper_id,
                    author_id=author_id
                )

    # Close the database connection
    print("Closing database connection...")
    manager.close_connection()
    print("Script completed successfully.")

if __name__ == '__main__':
    main()
