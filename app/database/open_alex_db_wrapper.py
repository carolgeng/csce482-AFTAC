# app/database/open_alex_db_wrapper.py

import sys
import requests
from .DatabaseManager import DatabaseManager
from .APIs.open_alex.open_alex_wrapper import OpenAlexAPIHandler

class OpenAlexDbWrapper:
    def __init__(self):
        self.api_handler = OpenAlexAPIHandler()
        self.db_manager = DatabaseManager()

    def run_query(self, query, max_results=None):
        """
        This method can be called by the frontend to initiate the data fetching process.
        """
        self.query_and_store(query, max_results)
        self.update_existing_entries()

    def query_and_store(self, query, max_results=None):
        """
        Fetch data from OpenAlex based on the query and store it in the database.
        """
        count = 0
        inserted_papers = 0
        print(f"Querying OpenAlex for: '{query}'...")
        try:
            for result in self.api_handler.query(query, max_results=max_results):
                count += 1

                try:
                    # Extract necessary fields from the OpenAlex work
                    paper_openalex_id = result.get('id', '').replace('https://openalex.org/', '')
                    title = result.get('title', 'No Title')

                    abstract_inverted_index = result.get('abstract_inverted_index', None)
                    abstract = self.reconstruct_abstract(abstract_inverted_index)

                    publication_year = result.get('publication_year', None)
                    doi = result.get('doi', None)
                    if not doi and not paper_openalex_id:
                        print(f"Paper '{title}' has no DOI or OpenAlex ID. Skipping.")
                        continue
                    pdf_url = result.get('primary_location', {}).get('pdf_url', None)

                    # Insert paper information into the database
                    paper_id = self.db_manager.insert_paper(
                        openalex_id=paper_openalex_id,
                        title=title,
                        abstract=abstract,
                        publication_year=publication_year,
                        total_citations=result.get('cited_by_count', 0),
                        influential_citations=len(result.get('referenced_works', [])),
                        pdf_url=pdf_url,
                        doi=doi
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
                        author_name = author_info.get('display_name', '').strip()
                        if not author_name:
                            print("Author name is missing. Skipping this author.")
                            continue

                        author_openalex_id = author_info.get('id', '')
                        if not author_openalex_id:
                            print("Author OpenAlex ID is missing. Skipping this author.")
                            continue

                        # Insert or update the author
                        author_id = self.db_manager.insert_author(
                            openalex_id=author_openalex_id,
                            name=author_name
                        )

                        if not author_id:
                            print(f"Failed to insert/update author: '{author_name}'. Skipping this author.")
                            continue

                        # Insert paper-author relationship
                        self.db_manager.insert_paper_author(paper_id, author_id)

                    # Insert concept (subject) information
                    for concept in result.get('concepts', []):
                        concept_name = concept.get('display_name', None)
                        if not concept_name:
                            print("Concept name is missing. Skipping this concept.")
                            continue

                        concept_openalex_id = concept.get('id', '')
                        if not concept_openalex_id:
                            print("Concept OpenAlex ID is missing. Skipping this concept.")
                            continue

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
                            score=concept.get('score', None)
                        )

                except Exception as e:
                    print(f"An error occurred while processing paper '{title}': {e}. Skipping this paper.")
                    continue

                if max_results is not None and count >= max_results:
                    break
        except Exception as e:
            print(f"An error occurred during querying: {e}")
        finally:
            print(f"Processed {count} results from OpenAlex. Inserted {inserted_papers} new papers into the database.")
            self.db_manager.close()

    def reconstruct_abstract(self, abstract_inverted_index):
        """
        Reconstruct the abstract from the inverted index provided by OpenAlex.
        """
        if not abstract_inverted_index:
            return None
        try:
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
            return abstract
        except Exception as e:
            print(f"Error reconstructing abstract: {e}")
            return None

    def update_existing_entries(self):
        """
        Update existing database entries with data from OpenAlex.
        """
        entries_to_update = self.db_manager.get_entries_with_placeholders()
        print(f"Found {len(entries_to_update)} papers with placeholders to update.")
        for entry in entries_to_update:
            paper_id, openalex_id, doi, title, publication_year = entry
            openalex_data = self.fetch_openalex_data(openalex_id, doi, title, publication_year)
            if openalex_data:
                self.db_manager.update_paper_entry(paper_id, openalex_data)

    def fetch_openalex_data(self, openalex_id, doi, title, publication_year):
        """
        Fetch OpenAlex data for a given paper entry.
        """
        try:
            if doi:
                response = requests.get(f"https://api.openalex.org/works/doi:{doi}")
            elif openalex_id:
                response = requests.get(f"https://api.openalex.org/works/{openalex_id}")
            elif title and publication_year:
                # Replace spaces with '+' for URL encoding
                encoded_title = title.replace(' ', '+')
                query = f"title.search:{encoded_title} AND publication_year:{publication_year}"
                response = requests.get(f"https://api.openalex.org/works?filter={query}")
            else:
                return None

            response.raise_for_status()
            data = response.json()

            if 'results' in data and data['results']:
                return data['results'][0]
            elif 'id' in data:
                return data
            else:
                return None
        except requests.RequestException as e:
            print(f"Error fetching data from OpenAlex: {e}")
            return None

if __name__ == "__main__":
    openalex_wrapper = OpenAlexDbWrapper()
    query = input("Enter the query string to search OpenAlex: ")
    try:
        max_results_input = input("Enter the maximum number of results to retrieve (press Enter for no limit): ")
        max_results = int(max_results_input) if max_results_input.strip() else None
    except ValueError:
        print("Invalid input for max_results. No limit will be applied.")
        max_results = None

    openalex_wrapper.run_query(query, max_results=max_results)
