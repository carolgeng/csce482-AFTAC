import sys
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.db.DatabaseManager import DatabaseManager
from app.APIs.crossref.crossref_wrapper import api_handler

def main():
    # Print the DATABASE_URL to ensure it's being correctly loaded
    database_url = os.getenv('DATABASE_URL')
    print("Using DATABASE_URL:", database_url)

    # Initialize the database manager and API handler
    manager = DatabaseManager()
    handler = api_handler()

    # Prompt the user for the query keyword
    query = input('Enter the query string to search CrossRef: ')

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
        # More processing here...

        # Check if a paper with the same DOI already exists
        existing_paper = manager.get_paper_by_doi(doi)

        if not existing_paper:
            # Insert the paper into the database
            inserted_papers += 1
            print(f"Inserting paper {inserted_papers}: {title}")
            # Insert logic here...
        else:
            print(f"Paper with DOI {doi} already exists.")

    # Print summary
    if processed_count == 0:
        print("No results found for the given query.")
    else:
        print(f"Processed {processed_count} results from CrossRef. Inserted {inserted_papers} new papers into the database.")

    # Close the database connection
    manager.close_connection()

if __name__ == '__main__':
    main()
