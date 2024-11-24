from .arXiv_db_wrapper import ArxivDbWrapper
from .crossref_db_wrapper import CrossRefDbWrapper
from .open_alex_db_wrapper import OpenAlexDbWrapper
from .semantic_scholar_db_wrapper import SemanticScholarDbWrapper

class DatabaseSearchService:
    def __init__(self, query: str, num_articles: int = 1000):
        self.query = query
        self.num_articles = num_articles

        # Initialize the database wrappers
        self.arxiv_db = ArxivDbWrapper()
        self.crossref_db = CrossRefDbWrapper()
        self.openalex_db = OpenAlexDbWrapper()
        self.semantic_scholar_db = SemanticScholarDbWrapper()

    def search_and_store(self):
        """Search and store results from all databases using the provided query and number of articles."""
        try:
            print(f"Searching for '{self.query}' and retrieving {self.num_articles} results...")

            # Query and store results in each database
            self.arxiv_db.query_and_store(self.query, self.num_articles)
            self.crossref_db.query_and_store(self.query, self.num_articles)
            self.openalex_db.query_and_store(self.query, self.num_articles)
            self.semantic_scholar_db.query_and_store(self.query, self.num_articles)

            print("Search completed and results stored in all databases.")

        except Exception as e:
            print(f"An error occurred during search: {e}")