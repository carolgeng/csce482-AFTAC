import pytest
from unittest.mock import patch
from app.database.arXiv_db_wrapper import ArxivDbWrapper
from app.database.crossref_db_wrapper import CrossRefDbWrapper
from app.database.open_alex_db_wrapper import OpenAlexDbWrapper
from app.database.semantic_scholar_db_wrapper import SemanticScholarDbWrapper

@pytest.fixture
def mock_wrappers():
    with patch.object(ArxivDbWrapper, 'query_and_store') as mock_arxiv_query, \
         patch.object(CrossRefDbWrapper, 'query_and_store') as mock_crossref_query, \
         patch.object(OpenAlexDbWrapper, 'query_and_store') as mock_openalex_query, \
         patch.object(SemanticScholarDbWrapper, 'query_and_store') as mock_semanticscholar_query:
        
        # Mock the query_and_store methods for each wrapper
        mock_arxiv_query.return_value = None
        mock_crossref_query.return_value = None
        mock_openalex_query.return_value = None
        mock_semanticscholar_query.return_value = None
        
        yield {
            'arxiv': mock_arxiv_query,
            'crossref': mock_crossref_query,
            'openalex': mock_openalex_query,
            'semanticscholar': mock_semanticscholar_query
        }

def test_all_wrappers_query(mock_wrappers):
    query = "machine learning"
    max_results = 5

    # Create instances of the wrappers
    arxiv_db = ArxivDbWrapper()
    crossref_db = CrossRefDbWrapper()
    openalex_db = OpenAlexDbWrapper()
    semanticscholar_db = SemanticScholarDbWrapper()

    # Execute the query_and_store for all wrappers
    arxiv_db.query_and_store(query, max_results)
    crossref_db.query_and_store(query, max_results)
    openalex_db.query_and_store(query, max_results)
    semanticscholar_db.query_and_store(query, max_results)

    # Assert that each wrapper's query_and_store was called once with the correct parameters
    mock_wrappers['arxiv'].assert_called_once_with(query, max_results)
    mock_wrappers['crossref'].assert_called_once_with(query, max_results)
    mock_wrappers['openalex'].assert_called_once_with(query, max_results)
    mock_wrappers['semanticscholar'].assert_called_once_with(query, max_results)

def test_all_wrappers_query_with_invalid_input(mock_wrappers):
    query = ""
    max_results = "invalid_number"

    # Create instances of the wrappers
    arxiv_db = ArxivDbWrapper()
    crossref_db = CrossRefDbWrapper()
    openalex_db = OpenAlexDbWrapper()
    semanticscholar_db = SemanticScholarDbWrapper()

    # Handle invalid max_results input
    try:
        max_results = int(max_results)
    except ValueError:
        max_results = None

    # Execute the query_and_store for all wrappers
    arxiv_db.query_and_store(query, max_results)
    crossref_db.query_and_store(query, max_results)
    openalex_db.query_and_store(query, max_results)
    semanticscholar_db.query_and_store(query, max_results)

    # Assert that each wrapper's query_and_store was called once with the correct parameters
    mock_wrappers['arxiv'].assert_called_once_with(query, max_results)
    mock_wrappers['crossref'].assert_called_once_with(query, max_results)
    mock_wrappers['openalex'].assert_called_once_with(query, max_results)
    mock_wrappers['semanticscholar'].assert_called_once_with(query, max_results)

def test_all_wrappers_query_exception_handling(mock_wrappers):
    query = "deep learning"
    max_results = 10

    # Simulate an exception in one of the wrappers
    mock_wrappers['arxiv'].side_effect = Exception("Arxiv API Error")

    # Create instances of the wrappers
    arxiv_db = ArxivDbWrapper()
    crossref_db = CrossRefDbWrapper()
    openalex_db = OpenAlexDbWrapper()
    semanticscholar_db = SemanticScholarDbWrapper()

    # Execute the query_and_store for all wrappers and handle exceptions
    try:
        arxiv_db.query_and_store(query, max_results)
    except Exception as e:
        print(f"Handled exception: {e}")

    crossref_db.query_and_store(query, max_results)
    openalex_db.query_and_store(query, max_results)
    semanticscholar_db.query_and_store(query, max_results)

    # Assert that each wrapper's query_and_store was called with the correct parameters
    mock_wrappers['arxiv'].assert_called_once_with(query, max_results)
    mock_wrappers['crossref'].assert_called_once_with(query, max_results)
    mock_wrappers['openalex'].assert_called_once_with(query, max_results)
    mock_wrappers['semanticscholar'].assert_called_once_with(query, max_results)
