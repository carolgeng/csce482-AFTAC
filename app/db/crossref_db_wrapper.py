# CrossRefDbWrapper.py

import sys
import os
import hashlib

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.db.DatabaseManager import DatabaseManager  # Adjust the import path as necessary
from app.APIs.crossref.crossref_wrapper import api_handler  # Assuming you saved the CrossRef API handler as CrossRefApiHandler.py

class CrossRefDbWrapper:
    def __init__(self):
        self.api_handler = api_handler()
        self.db_manager = DatabaseManager()

    def generate_openalex_id(self, prefix, identifier):
        """
        Generate a unique openalex_id using SHA-256 hashing.
        Args:
            prefix (str): A prefix to distinguish the type (e.g., 'CROSSREF_AUTHOR_', 'CROSSREF_CONCEPT_').
            identifier (str): The string to hash (e.g., author name, category).
        Returns:
            str: A unique openalex_id.
        """
        hash_object = hashlib.sha256(identifier.encode())
        hex_dig = hash_object.hexdigest()
        return f"{prefix}{hex_dig[:10]}"  # Truncate for brevity

    def query_and_store(self, query, max_results=None):
        count = 0
        inserted_papers = 0
        print(f"Querying CrossRef for: {query}...")
        try:
            for result in self.api_handler.query(query, max_results=max_results):
                count += 1

                try:
                    # Insert paper information into the database
                    paper_openalex_id = self.generate_openalex_id('CROSSREF_PAPER_', result.get('DOI', ''))
                    inserted_papers += 1
                    print(f"\nInserting paper {inserted_papers}: {result.get('title', ['No Title'])[0]}")
                    paper_id = self.db_manager.insert_paper(
                        openalex_id=paper_openalex_id,
                        title=result.get('title', ['No Title'])[0],
                        abstract=result.get('abstract', None),
                        publication_year=self.extract_year(result.get('published', {}).get('date-parts', [[None]])[0][0]),
                        journal_id=None,  # Assuming journal info is not directly available or requires separate handling
                        total_citations=0,  # Placeholder as CrossRef does not provide citation counts
                        citations_per_year=0.0,  # Placeholder
                        rank_citations_per_year=0,  # Placeholder
                        pdf_url=self.extract_pdf_url(result.get('link', [])),
                        doi=result.get('DOI', None),
                        influential_citations=0,  # Placeholder
                        delta_citations=0  # Placeholder
                    )

                    if not paper_id:
                        print(f"\nFailed to insert/update paper: {result.get('title', ['No Title'])[0]}. Skipping further processing for this paper.")
                        continue

                    # Insert author information
                    for author in result.get('author', []):
                        author_name = self.format_author_name(author)
                        if not author_name:
                            print("Author name is missing. Skipping this author.")
                            continue

                        # Generate a unique openalex_id for the author
                        author_openalex_id = self.generate_openalex_id('CROSSREF_AUTHOR_', author_name)

                        # Insert or update the author
                        author_id = self.db_manager.insert_author(
                            openalex_id=author_openalex_id,
                            name=author_name,
                            first_publication_year=0,  # Using 0 as a placeholder
                            author_age=0,  # Using 0 as a placeholder
                            h_index=0,  # Using 0 as a placeholder
                            delta_h_index=0,  # Using 0 as a placeholder
                            adopters=0,  # Using 0 as a placeholder
                            total_papers=0,  # Using 0 as a placeholder
                            delta_total_papers=0,  # Using 0 as a placeholder
                            recent_coauthors=0,  # Using 0 as a placeholder
                            coauthor_pagerank=0.0,  # Using 0.0 as a placeholder
                            total_citations=0,  # Using 0 as a placeholder
                            citations_per_paper=0.0,  # Using 0.0 as a placeholder
                            max_citations=0,  # Using 0 as a placeholder
                            total_journals=0  # Using 0 as a placeholder
                        )

                        if not author_id:
                            print(f"Failed to insert/update author: {author_name}. Skipping this author.")
                            continue

                        # Insert paper-author relationship
                        self.db_manager.insert_paper_author(paper_id=paper_id, author_id=author_id)

                    # Insert subject (category) information
                    for subject in result.get('subject', []):
                        if not subject:
                            print("Subject is missing. Skipping this subject.")
                            continue

                        # Generate a unique openalex_id for the subject
                        subject_openalex_id = self.generate_openalex_id('CROSSREF_CONCEPT_', subject)

                        # Insert or update the concept
                        concept_id = self.db_manager.insert_concept(
                            openalex_id=subject_openalex_id,
                            name=subject
                        )

                        if not concept_id:
                            print(f"Failed to insert/update concept: {subject}. Skipping this concept.")
                            continue

                        # Insert paper-concept relationship
                        self.db_manager.insert_paper_concept(
                            paper_id=paper_id,
                            concept_id=concept_id,
                            score=None  # Placeholder as CrossRef does not provide a score
                        )

                except Exception as e:
                    print(f"An error occurred while processing paper '{result.get('title', ['No Title'])[0]}': {e}. Skipping this paper.")

                if max_results is not None and count >= max_results:
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print(f"Processed {count} results from CrossRef. Inserted {inserted_papers} new papers into the database.")
            self.db_manager.close()

    def extract_year(self, date_part):
        """
        Extract the year from the date-parts list.
        Args:
            date_part (list or int): The date parts from CrossRef API.
        Returns:
            int or None: The publication year.
        """
        try:
            if isinstance(date_part, list):
                return date_part[0]
            return int(date_part)
        except (IndexError, ValueError, TypeError):
            return None

    def extract_pdf_url(self, links):
        """
        Extract the PDF URL from the list of links.
        Args:
            links (list): List of link dictionaries from CrossRef API.
        Returns:
            str or None: The PDF URL if available.
        """
        for link in links:
            if link.get('content-type') == 'application/pdf':
                return link.get('URL')
        return None

    def format_author_name(self, author):
        """
        Format the author's name from the CrossRef API response.
        Args:
            author (dict): Author information from CrossRef API.
        Returns:
            str: Formatted author name.
        """
        given = author.get('given', '').strip()
        family = author.get('family', '').strip()
        if given and family:
            return f"{given} {family}"
        elif family:
            return family
        elif given:
            return given
        return None

if __name__ == "__main__":
    crossref_wrapper = CrossRefDbWrapper()
    query = input("Enter the query string to search CrossRef: ")
    try:
        max_results_input = input("Enter the maximum number of results to retrieve (press Enter for default 1000): ")
        max_results = int(max_results_input) if max_results_input.strip() else None
    except ValueError:
        print("Invalid input for max_results. Using default value.")
        max_results = None

    crossref_wrapper.query_and_store(query, max_results=max_results)
