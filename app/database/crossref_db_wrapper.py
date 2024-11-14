import sys
import os
import requests
from datetime import datetime

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.database.DatabaseManager import DatabaseManager
from app.APIs.crossref.crossref_wrapper import api_handler

def extract_date(date_parts):
    """Extracts the year from the 'date-parts' field."""
    if date_parts and isinstance(date_parts, list) and len(date_parts) > 0:
        return date_parts[0][0]  # Returns the year
    return None

def main():
    # Prompt the user for the query keyword
    query = input('Enter the query string to search CrossRef: ')

    # Initialize the database manager and API handler
    manager = DatabaseManager("data.db")
    handler = api_handler()

    # Start querying
    print(f"Querying CrossRef for: {query}...")
    results_generator = handler.query(query, None)

    processed_count = 0
    inserted_papers = 0

    # Process results iteratively
    for result in results_generator:
        processed_count += 1

        # Extract relevant fields from the result
        doi = result.get("DOI")
        title = ' '.join(result.get("title", ["No Title"])) if "title" in result else "No Title"
        abstract = result.get("abstract", None)
        publication_year = extract_date(result.get("published-print", {}).get("date-parts")) or \
                           extract_date(result.get("published-online", {}).get("date-parts"))
        journal_info = result.get("container-title", [])
        journal_name = journal_info[0] if journal_info else None
        pdf_url = result.get("URL", None)  # CrossRef provides a URL field which can be used as a link to the paper

        # Check if a paper with the same DOI already exists
        existing_paper = manager.get_paper_by_doi(doi)

        if not existing_paper:
            # Insert the journal into the database and get its ID
            journal_id = None
            if journal_name:
                journal_id = manager.get_or_create_journal(
                    journal_name=journal_name,
                    mean_citations_per_paper=0.0,  # Placeholder; update as needed
                    delta_mean_citations_per_paper=0.0,  # Placeholder
                    journal_h_index=0,  # Placeholder
                    delta_journal_h_index=0,  # Placeholder
                    max_citations_paper=0,  # Placeholder
                    total_papers_published=0,  # Placeholder
                    delta_total_papers_published=0  # Placeholder
                )

            # Insert the paper into the database
            inserted_papers += 1
            print(f"Inserting paper {inserted_papers}: {title}")
            paper_id = manager.insert_paper(
                corpus_id=None,  # Replace with an actual corpus_id if available
                title=title,
                abstract=abstract,
                publication_year=publication_year,
                journal_id=journal_id,
                total_citations=result.get("is-referenced-by-count", 0),
                influential_citations=0,  # Placeholder; update as needed
                delta_citations=0,  # Placeholder
                citations_per_year=0.0,  # Placeholder
                rank_citations_per_year=None,  # Placeholder
                pdf_url=pdf_url,
                doi=doi
            )
        else:
            # Use the existing paper ID if found
            paper_id = existing_paper['id']

        # Process authors (insert or get existing authors and paper_authors associations)
        if "author" in result and result["author"] is not None:
            for author in result["author"]:
                given_name = author.get("given", "")
                family_name = author.get("family", "")
                author_name = f"{given_name} {family_name}".strip()
                affiliation = author.get("affiliation", [])
                affiliation_name = affiliation[0].get("name") if affiliation else None

                
                author_id = manager.get_or_create_author(
                    name=author_name,
                    first_publication_year=0,  # Placeholder; update as needed
                    author_age=0,  # Placeholder; update as needed
                    h_index=0,  # Placeholder; update as needed
                    delta_h_index=0,  # Placeholder
                    adopters=0,  # Placeholder
                    total_papers=0,  # Placeholder
                    delta_total_papers=0,  # Placeholder
                    recent_coauthors=0,  # Placeholder
                    coauthor_pagerank=0.0,  # Placeholder
                    total_citations=0  # Placeholder
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
        print(f"Processed {processed_count} results from CrossRef. Inserted {inserted_papers} new papers into the database.")

    # Close the database connection
    manager.close_connection()

if __name__ == '__main__':
    main()
