import sys
import os

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.db.DatabaseManager import DatabaseManager
from app.APIs.arXiv.arXiv_wrapper import api_handler

class ArxivDbWrapper:
    def __init__(self):
        self.api_handler = api_handler()
        self.db_manager = DatabaseManager()

    def query_and_store(self, query, max_results=None):
        count = 0
        inserted_papers = 0
        print(f"Querying arXiv for: {query}...")
        try:
            for result in self.api_handler.query(query, max_results=max_results):
                count += 1

                try:
                    # Insert paper information into the database
                    existing_paper = self.db_manager.get_paper_by_doi(result.doi) if hasattr(self.db_manager, 'get_paper_by_doi') else None

                    if not existing_paper:
                        inserted_papers += 1
                        print(f"Inserting paper {inserted_papers}: {result.title}")
                        self.db_manager.insert_paper(
                            openalex_id=result.entry_id,
                            title=result.title,
                            abstract=result.summary,
                            publication_year=result.published.year,
                            journal_id=None,  # Assuming journal info is not available directly from arXiv
                            total_citations=0,  # Assuming we don't have citation info from arXiv
                            citations_per_year=0.0,  # Assuming we don't have citation info from arXiv
                            rank_citations_per_year=0,  # Placeholder
                            pdf_url=result.pdf_url,
                            doi=result.doi,
                            influential_citations=0,  # Placeholder
                            delta_citations=0  # Placeholder
                        )
                    else:
                        print(f"Paper already exists in the database: {result.title}")
                        # Update missing fields if they exist in the query result
                        self.db_manager.update_paper_if_missing(
                            existing_paper_id=existing_paper[0],
                            openalex_id=result.entry_id,
                            title=result.title,
                            abstract=result.summary,
                            publication_year=result.published.year,
                            pdf_url=result.pdf_url,
                            doi=result.doi
                        )

                    # Insert author information
                    for author in result.authors:
                        author_name = author.name
                        try:
                            author_id = self.db_manager.get_or_create_author(
                                openalex_id="dummy_id",  # Using a simple dummy value to avoid URL syntax issues
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
                                total_journals=0,  # Using 0 as a placeholder
                                mean_journal_citations_per_paper=0.0  # Using 0.0 as a placeholder
                            )

                            # Insert paper-author relationship
                            self.db_manager.insert_or_ignore_paper_author(
                                paper_id=result.entry_id,
                                author_id=author_id
                            )
                        except Exception as e:
                            print(f"An error occurred while processing author '{author_name}': {e}. Skipping this author.")

                    # Insert concept (category) information
                    for category in result.categories:
                        try:
                            self.db_manager.insert_concept(
                                openalex_id="concept_dummy_id",  # Using a simple dummy value to avoid URL syntax issues
                                name=category  # Using category as both ID and name for simplicity
                            )

                            # Insert paper-concept relationship
                            self.db_manager.insert_paper_concept(
                                paper_id=result.entry_id,
                                concept_id=category,
                                score=None  # Placeholder as we don't have a score
                            )
                        except Exception as e:
                            print(f"An error occurred while processing concept '{category}': {e}. Skipping this concept.")
                except Exception as e:
                    print(f"An error occurred while processing paper '{result.title}': {e}. Skipping this paper.")

                if max_results is not None and count >= max_results:
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print(f"Processed {count} results from arXiv. Inserted {inserted_papers} new papers into the database.")
            self.db_manager.close_connection()

if __name__ == "__main__":
    arxiv_wrapper = ArxivDbWrapper()
    query = input("Enter the query string to search arXiv: ")
    arxiv_wrapper.query_and_store(query, max_results=5)
