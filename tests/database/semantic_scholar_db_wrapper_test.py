import pytest
from unittest.mock import patch, MagicMock
from app.database.semantic_scholar_db_wrapper import SemanticScholarDbWrapper
from app.database.DatabaseManager import DatabaseManager
from app.APIs.semantic_scholar.semantic_scholar_wrapper import api_handler

@pytest.fixture
def semantic_scholar_wrapper():
    with patch.object(DatabaseManager, "__init__", lambda x: None), \
         patch.object(api_handler, "__init__", lambda x, api_key=None: None):
        wrapper = SemanticScholarDbWrapper()
        wrapper.db_manager = MagicMock(spec=DatabaseManager)
        wrapper.api_handler = MagicMock(spec=api_handler)
        return wrapper

def test_generate_openalex_id(semantic_scholar_wrapper):
    prefix = "SEM_SCHOLAR_AUTHOR_"
    identifier = "John Doe"
    openalex_id = semantic_scholar_wrapper.generate_openalex_id(prefix, identifier)
    assert openalex_id.startswith(prefix)
    assert len(openalex_id) > len(prefix)

def test_query_and_store_paper(semantic_scholar_wrapper):
    mock_result = {
        "externalIds": {"DOI": "10.1234/sem_scholar.123"},
        "title": "Sample Paper",
        "abstract": "This is a summary of the paper.",
        "year": 2023,
        "authors": [{"name": "John Doe"}, {"name": "Jane Doe"}],
        "url": "http://example.com/paper.pdf",
        "influentialCitationCount": 5
    }

    semantic_scholar_wrapper.api_handler.query.return_value = [mock_result]
    semantic_scholar_wrapper.db_manager.insert_paper.return_value = 1
    semantic_scholar_wrapper.db_manager.insert_author.return_value = 2
    semantic_scholar_wrapper.db_manager.insert_paper_author.return_value = None

    with patch.object(semantic_scholar_wrapper.db_manager, 'insert_author', wraps=semantic_scholar_wrapper.db_manager.insert_author) as mock_insert_author:
        with patch.object(semantic_scholar_wrapper.db_manager, 'insert_paper_author', wraps=semantic_scholar_wrapper.db_manager.insert_paper_author) as mock_insert_paper_author:
            semantic_scholar_wrapper.query_and_store(query="machine learning", max_results=1)
            
            # Check that the insert methods were called
            semantic_scholar_wrapper.db_manager.insert_paper.assert_called_once()
            assert mock_insert_author.call_count == len(mock_result['authors'])
            assert mock_insert_paper_author.call_count == len(mock_result['authors'])

def test_query_and_store_with_missing_data(semantic_scholar_wrapper):
    mock_result = {
        "externalIds": {},  # Missing DOI
        "title": "No Title",  # Default title if missing
        "abstract": None,
        "year": None,  # Missing publication year
        "authors": []  # Missing author data
    }

    semantic_scholar_wrapper.api_handler.query.return_value = [mock_result]
    semantic_scholar_wrapper.db_manager.insert_paper.return_value = None  # Paper insertion fails

    semantic_scholar_wrapper.query_and_store(query="artificial intelligence", max_results=1)

    # Check that paper insertion was attempted and failed
    semantic_scholar_wrapper.db_manager.insert_paper.assert_not_called()
    # Author insertion should not be called due to missing data
    semantic_scholar_wrapper.db_manager.insert_author.assert_not_called()
    semantic_scholar_wrapper.db_manager.insert_paper_author.assert_not_called()

def test_query_and_store_exception_handling(semantic_scholar_wrapper):
    semantic_scholar_wrapper.api_handler.query.side_effect = Exception("API Error")

    semantic_scholar_wrapper.query_and_store(query="quantum computing", max_results=1)

    # Ensure that no inserts were attempted due to the exception
    semantic_scholar_wrapper.db_manager.insert_paper.assert_not_called()
    semantic_scholar_wrapper.db_manager.insert_author.assert_not_called()
    semantic_scholar_wrapper.db_manager.insert_paper_author.assert_not_called()

def test_generate_openalex_id_uniqueness(semantic_scholar_wrapper):
    prefix = "SEM_SCHOLAR_CONCEPT_"
    identifier1 = "Concept A"
    identifier2 = "Concept B"
    openalex_id1 = semantic_scholar_wrapper.generate_openalex_id(prefix, identifier1)
    openalex_id2 = semantic_scholar_wrapper.generate_openalex_id(prefix, identifier2)
    assert openalex_id1 != openalex_id2

def test_db_manager_close(semantic_scholar_wrapper):
    semantic_scholar_wrapper.db_manager.close = MagicMock()
    semantic_scholar_wrapper.query_and_store(query="deep learning", max_results=1)
    semantic_scholar_wrapper.db_manager.close.assert_called_once()
