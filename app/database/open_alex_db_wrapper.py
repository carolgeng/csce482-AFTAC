import sys
import os

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.database.DatabaseManager import DatabaseManager
from app.APIs.open_alex.open_alex_wrapper import openalex_api_handler

def main():
    # Prompt the user for the query keyword
    query = input('Enter the query string to search OpenAlex: ')

    # Initialize the database manager and API handler
    manager = DatabaseManager("data.db")
    handler = openalex_api_handler()

    # Start querying
    print(f"Querying OpenAlex for: {query}...")
    results_generator = handler.query(query, None)

    processed_count = 0
    inserted_papers = 0

    # Process results iteratively
    for result in results_generator:
        processed_count += 1

        # Extract relevant fields from the result
        openalex_id = result.get('id')  # e.g., "https://openalex.org/Wxxxxxx"
        doi = result.get('doi')
        title = result.get('title') or 'No Title'  # Use 'No Title' if None or not provided
        if title is None or title.strip() == "":
            title = "No Title"

        # Construct the abstract string from the abstract_inverted_index
        abstract = extract_abstract(result.get('abstract_inverted_index', None))

        publication_year = result.get('publication_year')
        total_citations = result.get('cited_by_count', 0)

        # Attempt to extract a PDF URL if available
        pdf_url = extract_pdf_url(result)

        # Attempt to extract journal information if available
        journal_id = None
        host_venue = result.get('host_venue', None)
        if host_venue:
            journal_name = host_venue.get('display_name')
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

        # Check if a paper with the same DOI already exists
        existing_paper = manager.get_paper_by_doi(doi)

        if not existing_paper:
            # Insert the paper into the database
            inserted_papers += 1
            print(f"Inserting paper {inserted_papers}: {title}")
            paper_id = manager.insert_paper(
                corpus_id=openalex_id,
                title=title,
                abstract=abstract,
                publication_year=publication_year,
                journal_id=journal_id,
                total_citations=total_citations,
                influential_citations=0,
                delta_citations=0,
                citations_per_year=0.0,
                rank_citations_per_year=None,
                pdf_url=pdf_url,
                doi=doi
            )
        else:
            # Use the existing paper ID if found
            paper_id = existing_paper['id']

        # Process authors (insert or get existing authors and paper_authors associations)
        authorships = result.get('authorships', [])
        for authorship in authorships:
            author_data = authorship.get('author', {})
            author_name = author_data.get('display_name') or 'Unknown Author'

            # Attempt to get the author's OpenAlex ID (if needed)
            author_openalex_id = author_data.get('id')
            
            author_id = manager.get_or_create_author(
                name=author_name,
                first_publication_year=None,   # Placeholder
                author_age=None,               # Placeholder
                h_index=0,                     # Placeholder
                delta_h_index=None,            # Placeholder
                adopters=0,                    # Placeholder
                total_papers=0,                # Placeholder
                delta_total_papers=None,       # Placeholder
                recent_coauthors=None,         # Placeholder
                coauthor_pagerank=0.0,         # Placeholder
                total_citations=0              # Placeholder
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
        print(f"Processed {processed_count} results from OpenAlex. Inserted {inserted_papers} new papers into the database.")

    # Close the database connection
    manager.close_connection()

def extract_abstract(abstract_inverted_index):
    """
    Extracts a readable abstract from the OpenAlex `abstract_inverted_index` if available.
    """
    if not abstract_inverted_index:
        return None

    # `abstract_inverted_index` is a dictionary where keys are words and values are lists of positions.
    # We need to reconstruct the abstract from these positions.
    word_positions = []
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))

    # Sort words by their position
    word_positions.sort(key=lambda x: x[0])
    # Join the words to form the abstract text
    abstract = " ".join([w[1] for w in word_positions])
    return abstract

def extract_pdf_url(work_result):
    """
    Extracts a PDF or best available URL from the given OpenAlex work result.
    """
    # Check if there's a direct PDF URL under primary_location
    primary_location = work_result.get('primary_location', {})
    pdf_url = primary_location.get('pdf_url', None)

    # If no pdf_url, check if any host_urls might be appropriate
    if not pdf_url:
        host_venue = work_result.get('host_venue', {})
        if host_venue:
            pdf_url = host_venue.get('url', None)  # Use the host venue URL if provided
    return pdf_url

if __name__ == '__main__':
    main()
