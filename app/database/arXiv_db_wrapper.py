# ArxivDbWrapper.py

import hashlib
from .DatabaseManager import DatabaseManager
from .APIs.arXiv.arXiv_wrapper import api_handler

class ArxivDbWrapper:
    def __init__(self):
        self.api_handler = api_handler()
        self.db_manager = DatabaseManager()

    def generate_openalex_id(self, prefix, identifier):
        """
        Generate a unique openalex_id using SHA-256 hashing.
        Args:
            prefix (str): A prefix to distinguish the type (e.g., 'ARXIV_AUTHOR_', 'ARXIV_CONCEPT_').
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
        print(f"Querying arXiv for: {query}...")
        try:
            for result in self.api_handler.query(query, max_results=max_results):
                count += 1

                try:
                    # Insert paper information into the database
                    paper_openalex_id = result.entry_id  # Assuming entry_id is unique and suitable
                    inserted_papers += 1
                    print(f"\nInserting paper {inserted_papers}: {result.title}")
                    paper_id = self.db_manager.insert_paper(
                        openalex_id=paper_openalex_id,
                        title=result.title,
                        abstract=result.summary,
                        publication_year=result.published.year if result.published else None,
                        journal_id=None,  # Assuming journal info is not available directly from arXiv
                        total_citations=0,  # Assuming we don't have citation info from arXiv
                        citations_per_year=0.0,  # Assuming we don't have citation info from arXiv
                        rank_citations_per_year=0,  # Placeholder
                        pdf_url=result.pdf_url,
                        doi=result.doi if result.doi else None,
                        influential_citations=0,  # Placeholder
                        delta_citations=0  # Placeholder
                    )

                    if not paper_id:
                        print(f"\nFailed to insert/update paper: {result.title}. Skipping further processing for this paper.")
                        continue

                    # Insert author information
                    for author in result.authors:
                        author_name = author.name
                        if not author_name:
                            print("Author name is missing. Skipping this author.")
                            continue

                        # Generate a unique openalex_id for the author
                        author_openalex_id = self.generate_openalex_id('ARXIV_AUTHOR_', author_name)

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

                    # Insert concept (category) information
                    for category in result.categories:
                        if not category:
                            print("Category is missing. Skipping this category.")
                            continue

                        # Generate a unique openalex_id for the concept
                        concept_openalex_id = self.generate_openalex_id('ARXIV_CONCEPT_', category)

                        # Insert or update the concept
                        concept_id = self.db_manager.insert_concept(
                            openalex_id=concept_openalex_id,
                            name=category
                        )

                        if not concept_id:
                            print(f"Failed to insert/update concept: {category}. Skipping this concept.")
                            continue

                        # Insert paper-concept relationship
                        self.db_manager.insert_paper_concept(
                            paper_id=paper_id,
                            concept_id=concept_id,
                            score=None  # Placeholder as we don't have a score
                        )

                except Exception as e:
                    print(f"An error occurred while processing paper '{result.title}': {e}. Skipping this paper.")

                if max_results is not None and count >= max_results:
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print(f"Processed {count} results from arXiv. Inserted {inserted_papers} new papers into the database.")
            self.db_manager.close()

if __name__ == "__main__":
    arxiv_wrapper = ArxivDbWrapper()
    query = input("Enter the query string to search arXiv: ")

    try:
        max_results_input = input("Enter the maximum number of results to retrieve (press Enter for default 1000): ")
        max_results = int(max_results_input) if max_results_input.strip() else None
    except ValueError:
        print("Invalid input for max_results. Using default value.")
        max_results = None
    
    arxiv_wrapper.query_and_store(query, max_results)

    
