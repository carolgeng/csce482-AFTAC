# OpenAlexDbWrapper.py

import sys
import os
import hashlib

# Add the project root to sys.path
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
# sys.path.append(project_root)

from .DatabaseManager import DatabaseManager
from .APIs.open_alex.open_alex_wrapper import openalex_api_handler  # Ensure the correct path

class OpenAlexDbWrapper:
    def __init__(self):
        self.api_handler = openalex_api_handler()
        self.db_manager = DatabaseManager()

    def generate_openalex_id(self, prefix, identifier):
        """
        Generate a unique openalex_id using SHA-256 hashing.
        
        Args:
            prefix (str): A prefix to distinguish the type (e.g., 'OPENALEX_AUTHOR_', 'OPENALEX_CONCEPT_').
            identifier (str): The string to hash (e.g., author name, concept name).
        
        Returns:
            str: A unique openalex_id.
        """
        hash_object = hashlib.sha256(identifier.encode())
        hex_dig = hash_object.hexdigest()
        return f"{prefix}{hex_dig[:10]}"  # Truncate for brevity

    def query_and_store(self, query, max_results=None):
        count = 0
        inserted_papers = 0
        print(f"Querying OpenAlex for: '{query}'...")
        try:
            for result in self.api_handler.query(query, max_results=max_results):
                count += 1

                try:
                    # Extract necessary fields from the OpenAlex work
                    paper_openalex_id = result.get('id', '')
                    title = result.get('title', ['No Title'])[0] if isinstance(result.get('title'), list) else result.get('title', 'No Title')
                    
                    # Option 1: Use 'displayed_abstract' if available
                    abstract = result.get('displayed_abstract', None)
                    
                    # Option 2: Serialize 'abstract_inverted_index'
                    # abstract_dict = result.get('abstract_inverted_index', None)
                    # abstract = json.dumps(abstract_dict) if abstract_dict else None
                    
                    publication_year = self.extract_year(result.get('publication_year', None))
                    doi = result.get('doi', None)
                    pdf_url = self.extract_pdf_url(result.get('host_venue', {}).get('url', None))  # OpenAlex may not provide direct PDF URLs

                    # Insert paper information into the database
                    paper_id = self.db_manager.insert_paper(
                        openalex_id=paper_openalex_id,
                        title=title,
                        abstract=abstract,  # Ensure this is a string or None
                        publication_year=publication_year,
                        journal_id=None,  # OpenAlex provides host_venue, which can be mapped to journals if needed
                        total_citations=result.get('cited_by_count', 0),
                        citations_per_year=result.get('cited_by_count', 0) / (2024 - publication_year) if publication_year else 0.0,
                        rank_citations_per_year=0,  # Placeholder as OpenAlex does not provide rank
                        pdf_url=pdf_url,
                        doi=doi,
                        influential_citations=result.get('cited_by_influential_count', 0),
                        delta_citations=0  # Placeholder; requires tracking over time
                    )

                    if paper_id:
                        inserted_papers += 1
                        print(f"\nInserting paper {inserted_papers}: '{title}' with ID: {paper_id}.")
                    else:
                        print(f"\nFailed to insert/update paper: '{title}'. Skipping further processing for this paper.")
                        continue

                    # Insert author information
                    for author in result.get('authorships', []):
                        author_info = author.get('author', {})
                        author_name = self.format_author_name(author_info)
                        if not author_name:
                            print("Author name is missing. Skipping this author.")
                            continue

                        # Generate a unique openalex_id for the author
                        author_openalex_id = self.generate_openalex_id('OPENALEX_AUTHOR_', author_info.get('id', ''))

                        # Insert or update the author
                        author_id = self.db_manager.insert_author(
                            openalex_id=author_openalex_id,
                            name=author_name,
                            first_publication_year=0,  # Placeholder as OpenAlex may not provide this directly
                            author_age=0,  # Placeholder
                            h_index=0,  # Placeholder
                            delta_h_index=0,  # Placeholder
                            adopters=0,  # Placeholder
                            total_papers=0,  # Placeholder
                            delta_total_papers=0,  # Placeholder
                            recent_coauthors=0,  # Placeholder
                            coauthor_pagerank=0.0,  # Placeholder
                            total_citations=0,  # Placeholder
                            citations_per_paper=0.0,  # Placeholder
                            max_citations=0,  # Placeholder
                            total_journals=0  # Placeholder
                        )

                        if not author_id:
                            print(f"Failed to insert/update author: '{author_name}'. Skipping this author.")
                            continue

                        # Insert paper-author relationship
                        self.db_manager.insert_paper_author(paper_id=paper_id, author_id=author_id)

                    # Insert concept (subject) information
                    for concept in result.get('concepts', []):
                        concept_name = concept.get('display_name', None)
                        if not concept_name:
                            print("Concept name is missing. Skipping this concept.")
                            continue

                        # Generate a unique openalex_id for the concept
                        concept_openalex_id = self.generate_openalex_id('OPENALEX_CONCEPT_', concept.get('id', ''))

                        # Insert or update the concept
                        concept_id = self.db_manager.insert_concept(
                            openalex_id=concept_openalex_id,
                            name=concept_name
                        )

                        if not concept_id:
                            print(f"Failed to insert/update concept: '{concept_name}'. Skipping this concept.")
                            continue

                        # Insert paper-concept relationship
                        self.db_manager.insert_paper_concept(
                            paper_id=paper_id,
                            concept_id=concept_id,
                            score=None  # Placeholder as OpenAlex does not provide a score
                        )

                except Exception as e:
                    print(f"An error occurred while processing paper '{title}': {e}. Skipping this paper.")

                if max_results is not None and count >= max_results:
                    break
        except Exception as e:
            print(f"An error occurred during querying: {e}")
        finally:
            print(f"Processed {count} results from OpenAlex. Inserted {inserted_papers} new papers into the database.")
            self.db_manager.close()

    def extract_year(self, publication_year):
        """
        Extract and validate the publication year.
        
        Args:
            publication_year (int or None): The publication year from OpenAlex.
        
        Returns:
            int or None: The publication year if valid, else None.
        """
        if isinstance(publication_year, int) and 1000 < publication_year <= 2024:
            return publication_year
        return None

    def extract_pdf_url(self, host_venue_url):
        """
        Extract the PDF URL. OpenAlex may not provide direct PDF URLs, so this is a placeholder.
        
        Args:
            host_venue_url (str or None): The URL of the host venue.
        
        Returns:
            str or None: The PDF URL if available, else None.
        """
        # OpenAlex does not provide direct PDF URLs. This function can be enhanced if such information is available.
        return None

    def format_author_name(self, author):
        """
        Format the author's name from the OpenAlex API response.
        
        Args:
            author (dict): Author information from OpenAlex API.
        
        Returns:
            str: Formatted author name.
        """
        display_name = author.get('display_name', '').strip()
        if display_name:
            return display_name
        return None

if __name__ == "__main__":
    openalex_wrapper = OpenAlexDbWrapper()
    query = input("Enter the query string to search OpenAlex: ")
    try:
        max_results_input = input("Enter the maximum number of results to retrieve (press Enter for default 1000): ")
        max_results = int(max_results_input) if max_results_input.strip() else None
    except ValueError:
        print("Invalid input for max_results. Using default value.")
        max_results = None

    openalex_wrapper.query_and_store(query, max_results=max_results)