import pytest
from unittest.mock import patch, MagicMock
from app.database.arXiv_db_wrapper import ArxivDbWrapper
from app.database.DatabaseManager import DatabaseManager
from app.APIs.arXiv.arXiv_wrapper import api_handler

@pytest.fixture
def arxiv_wrapper():
    with patch.object(DatabaseManager, "__init__", lambda x: None), \
         patch.object(api_handler, "__init__", lambda x: None):
        wrapper = ArxivDbWrapper()
        wrapper.db_manager = MagicMock(spec=DatabaseManager)
        wrapper.api_handler = MagicMock(spec=api_handler)
        return wrapper

def test_generate_openalex_id(arxiv_wrapper):
    prefix = "ARXIV_AUTHOR_"
    identifier = "John Doe"
    openalex_id = arxiv_wrapper.generate_openalex_id(prefix, identifier)
    assert openalex_id.startswith(prefix)
    assert len(openalex_id) > len(prefix)

def test_query_and_store_paper(arxiv_wrapper):
    mock_result = MagicMock()
    mock_result.entry_id = "arxiv123"
    mock_result.title = "Sample Paper"
    mock_result.summary = "This is a summary of the paper."
    mock_result.published = MagicMock()
    mock_result.published.year = 2023
    mock_result.pdf_url = "http://example.com/paper.pdf"
    mock_result.doi = "10.1234/arxiv.123"
    
    # Setting author names as attributes instead of using name parameter
    author_1 = MagicMock()
    author_1.name = "John Doe"
    author_2 = MagicMock()
    author_2.name = "Jane Doe"
    mock_result.authors = [author_1, author_2]
    
    mock_result.categories = ["Category1", "Category2"]
    
    arxiv_wrapper.api_handler.query.return_value = [mock_result]
    arxiv_wrapper.db_manager.insert_paper.return_value = 1
    arxiv_wrapper.db_manager.insert_author.return_value = 2
    arxiv_wrapper.db_manager.insert_concept.return_value = 3
    arxiv_wrapper.db_manager.insert_paper_author.return_value = None
    arxiv_wrapper.db_manager.insert_paper_concept.return_value = None
    
    with patch.object(arxiv_wrapper.db_manager, 'insert_author', wraps=arxiv_wrapper.db_manager.insert_author) as mock_insert_author:
        with patch.object(arxiv_wrapper.db_manager, 'insert_paper_author', wraps=arxiv_wrapper.db_manager.insert_paper_author) as mock_insert_paper_author:
            arxiv_wrapper.query_and_store(query="machine learning", max_results=1)
            
            # Check that the insert methods were called
            arxiv_wrapper.db_manager.insert_paper.assert_called_once()
            assert mock_insert_author.call_count == len(mock_result.authors)
            assert arxiv_wrapper.db_manager.insert_concept.call_count == len(mock_result.categories)
            assert mock_insert_paper_author.call_count == len(mock_result.authors)
            assert arxiv_wrapper.db_manager.insert_paper_concept.call_count == len(mock_result.categories)

def test_query_and_store_with_missing_data(arxiv_wrapper):
    mock_result = MagicMock()
    mock_result.entry_id = "arxiv456"
    mock_result.title = None  # Missing title
    mock_result.summary = None
    mock_result.published = None  # Missing publication year
    mock_result.pdf_url = None
    mock_result.doi = None
    
    # Setting author name to None to simulate missing author name
    author = MagicMock()
    author.name = None
    mock_result.authors = [author]  # Missing author name
    mock_result.categories = []  # No categories
    
    arxiv_wrapper.api_handler.query.return_value = [mock_result]
    arxiv_wrapper.db_manager.insert_paper.return_value = None  # Paper insertion fails
    
    arxiv_wrapper.query_and_store(query="artificial intelligence", max_results=1)
    
    # Check that paper insertion was attempted and failed
    arxiv_wrapper.db_manager.insert_paper.assert_called_once()
    # Author and concept insertion should not be called due to failed paper insertion
    arxiv_wrapper.db_manager.insert_author.assert_not_called()
    arxiv_wrapper.db_manager.insert_concept.assert_not_called()
    arxiv_wrapper.db_manager.insert_paper_author.assert_not_called()
    arxiv_wrapper.db_manager.insert_paper_concept.assert_not_called()

def test_query_and_store_exception_handling(arxiv_wrapper):
    arxiv_wrapper.api_handler.query.side_effect = Exception("API Error")
    
    arxiv_wrapper.query_and_store(query="quantum computing", max_results=1)
    
    # Ensure that no inserts were attempted due to the exception
    arxiv_wrapper.db_manager.insert_paper.assert_not_called()
    arxiv_wrapper.db_manager.insert_author.assert_not_called()
    arxiv_wrapper.db_manager.insert_concept.assert_not_called()
    arxiv_wrapper.db_manager.insert_paper_author.assert_not_called()
    arxiv_wrapper.db_manager.insert_paper_concept.assert_not_called()

def test_generate_openalex_id_uniqueness(arxiv_wrapper):
    prefix = "ARXIV_CONCEPT_"
    identifier1 = "Concept A"
    identifier2 = "Concept B"
    openalex_id1 = arxiv_wrapper.generate_openalex_id(prefix, identifier1)
    openalex_id2 = arxiv_wrapper.generate_openalex_id(prefix, identifier2)
    assert openalex_id1 != openalex_id2

def test_db_manager_close(arxiv_wrapper):
    arxiv_wrapper.db_manager.close = MagicMock()
    arxiv_wrapper.query_and_store(query="deep learning", max_results=1)
    arxiv_wrapper.db_manager.close.assert_called_once()
