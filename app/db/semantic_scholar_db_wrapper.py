import sys
import os
import hashlib

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.db.DatabaseManager import DatabaseManager
from app.APIs.semantic_scholar.semantic_scholar_wrapper import api_handler

class SemanticScholarDbWrapper:
    def __init__(self):
        self.api_handler = api_handler(api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
        self.db_manager = DatabaseManager()

    def generate_openalex_id(self, prefix, identifier):
        """
        Generate a unique openalex_id using SHA-256 hashing.
        Args:
            prefix (str): A prefix to distinguish the type (e.g., 'SEM_SCHOLAR_AUTHOR_', 'SEM_SCHOLAR_CONCEPT_').
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
        print(f"Querying Semantic Scholar for: {query}...")
        try:
            for result in self.api_handler.query(query, max_results=max_results):
                count += 1

                try:
                    # Insert paper information into the database
                    paper_openalex_id = result.get("externalIds", {}).get("DOI", None)  # Assuming DOI is unique and suitable
                    if not paper_openalex_id:
                        print(f"No DOI found for paper: {result.get('title', 'No Title')}. Skipping.")
                        continue

                    inserted_papers += 1
                    print(f"\nInserting paper {inserted_papers}: {result.get('title')}")
                    paper_id = self.db_manager.insert_paper(
                        openalex_id=paper_openalex_id,
                        title=result.get("title"),
                        abstract=result.get("abstract"),
                        publication_year=result.get("year"),
                        journal_id=None,  # Assuming journal info is not available directly from Semantic Scholar
                        total_citations=result.get("influentialCitationCount", 0),
                        citations_per_year=0.0,  # Placeholder
                        rank_citations_per_year=0,  # Placeholder
                        pdf_url=result.get("url"),
                        doi=paper_openalex_id,
                        influential_citations=0,  # Placeholder
                        delta_citations=0  # Placeholder
                    )

                    if not paper_id:
                        print(f"\nFailed to insert/update paper: {result.get('title')}. Skipping further processing for this paper.")
                        continue

                    # Insert author information
                    for author in result.get("authors", []):
                        author_name = author.get("name")
                        if not author_name:
                            print("Author name is missing. Skipping this author.")
                            continue

                        # Generate a unique openalex_id for the author
                        author_openalex_id = self.generate_openalex_id('SEM_SCHOLAR_AUTHOR_', author_name)

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

                except Exception as e:
                    print(f"An error occurred while processing paper '{result.get('title')}': {e}. Skipping this paper.")

                if max_results is not None and count >= max_results:
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print(f"Processed {count} results from Semantic Scholar. Inserted {inserted_papers} new papers into the database.")
            self.db_manager.close()

if __name__ == "__main__":
    sem_scholar_wrapper = SemanticScholarDbWrapper()
    query = input("Enter the query string to search Semantic Scholar: ")

    try:
        max_results_input = input("Enter the maximum number of results to retrieve (press Enter for default 1000): ")
        max_results = int(max_results_input) if max_results_input.strip() else None
    except ValueError:
        print("Invalid input for max_results. Using default value.")
        max_results = None
    
    sem_scholar_wrapper.query_and_store(query, max_results)
