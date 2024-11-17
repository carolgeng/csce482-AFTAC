import sys
import os

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from app.db.arXiv_db_wrapper import ArxivDbWrapper
from app.db.crossref_db_wrapper import CrossRefDbWrapper
from app.db.open_alex_db_wrapper import OpenAlexDbWrapper
from app.db.semantic_scholar_db_wrapper import SemanticScholarDbWrapper

query = input("Enter the query string to search: ")

try:
    quantity = input("Enter the maximum number of results to retrieve (press Enter for default 1000): ")
    quantity = int(quantity) if quantity.strip() else None
except ValueError:
    print("Invalid input for max_results. Using default value.")
    quantity = None

arxiv_db = ArxivDbWrapper()
crossref_db = CrossRefDbWrapper()
openalex_db = OpenAlexDbWrapper()
semantic_scholar_db = SemanticScholarDbWrapper()

arxiv_db.query_and_store(query, quantity)
crossref_db.query_and_store(query, quantity)
openalex_db.query_and_store(query, quantity)
semantic_scholar_db.query_and_store(query, quantity)


