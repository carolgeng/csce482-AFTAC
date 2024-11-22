import pytest
from unittest.mock import patch, MagicMock
from app.database.open_alex_db_wrapper import OpenAlexDbWrapper
from app.database.DatabaseManager import DatabaseManager
from app.database.APIs.open_alex.open_alex_wrapper import openalex_api_handler

@pytest.fixture
def openalex_wrapper():
    with patch.object(DatabaseManager, "__init__", lambda x: None), \
         patch.object(openalex_api_handler, "__init__", lambda x: None):
        wrapper = OpenAlexDbWrapper()
        wrapper.db_manager = MagicMock(spec=DatabaseManager)
        wrapper.api_handler = MagicMock(spec=openalex_api_handler)
        return wrapper

def test_generate_openalex_id(openalex_wrapper):
    prefix = "OPENALEX_AUTHOR_"
    identifier = "John Doe"
    openalex_id = openalex_wrapper.generate_openalex_id(prefix, identifier)
    assert openalex_id.startswith(prefix)
    assert len(openalex_id) > len(prefix)

def test_query_and_store_paper(openalex_wrapper):
    mock_result = {
        "id": "openalex123",
        "title": "Sample Paper",
        "displayed_abstract": "This is a summary of the paper.",
        "publication_year": 2023,
        "authorships": [{"author": {"id": "A123", "display_name": "John Doe"}},
                         {"author": {"id": "A124", "display_name": "Jane Doe"}}],
        "concepts": [{"id": "C123", "display_name": "Concept1"},
                      {"id": "C124", "display_name": "Concept2"}],
        "cited_by_count": 10,
        "cited_by_influential_count": 2
    }

    openalex_wrapper.api_handler.query.return_value = [mock_result]
    openalex_wrapper.db_manager.insert_paper.return_value = 1
    openalex_wrapper.db_manager.insert_author.return_value = 2
    openalex_wrapper.db_manager.insert_concept.return_value = 3
    openalex_wrapper.db_manager.insert_paper_author.return_value = None
    openalex_wrapper.db_manager.insert_paper_concept.return_value = None

    with patch.object(openalex_wrapper.db_manager, 'insert_author', wraps=openalex_wrapper.db_manager.insert_author) as mock_insert_author:
        with patch.object(openalex_wrapper.db_manager, 'insert_paper_author', wraps=openalex_wrapper.db_manager.insert_paper_author) as mock_insert_paper_author:
            openalex_wrapper.query_and_store(query="machine learning", max_results=1)
            
            # Check that the insert methods were called
            openalex_wrapper.db_manager.insert_paper.assert_called_once()
            assert mock_insert_author.call_count == len(mock_result['authorships'])
            assert openalex_wrapper.db_manager.insert_concept.call_count == len(mock_result['concepts'])
            assert mock_insert_paper_author.call_count == len(mock_result['authorships'])
            assert openalex_wrapper.db_manager.insert_paper_concept.call_count == len(mock_result['concepts'])

def test_query_and_store_with_missing_data(openalex_wrapper):
    mock_result = {
        "id": "openalex456",  # Provided ID
        "title": "No Title",  # Default title if missing
        "displayed_abstract": None,
        "publication_year": None,  # Missing publication year
        "authorships": [],  # Missing author data
        "concepts": []  # No subjects
    }

    openalex_wrapper.api_handler.query.return_value = [mock_result]
    openalex_wrapper.db_manager.insert_paper.return_value = 1  # Paper insertion succeeds even with missing fields

    openalex_wrapper.query_and_store(query="artificial intelligence", max_results=1)

    # Check that paper insertion was attempted and succeeded
    openalex_wrapper.db_manager.insert_paper.assert_called_once()
    # Author and concept insertion should not be called due to missing data
    openalex_wrapper.db_manager.insert_author.assert_not_called()
    openalex_wrapper.db_manager.insert_concept.assert_not_called()
    openalex_wrapper.db_manager.insert_paper_author.assert_not_called()
    openalex_wrapper.db_manager.insert_paper_concept.assert_not_called()

def test_query_and_store_exception_handling(openalex_wrapper):
    openalex_wrapper.api_handler.query.side_effect = Exception("API Error")

    openalex_wrapper.query_and_store(query="quantum computing", max_results=1)

    # Ensure that no inserts were attempted due to the exception
    openalex_wrapper.db_manager.insert_paper.assert_not_called()
    openalex_wrapper.db_manager.insert_author.assert_not_called()
    openalex_wrapper.db_manager.insert_concept.assert_not_called()
    openalex_wrapper.db_manager.insert_paper_author.assert_not_called()
    openalex_wrapper.db_manager.insert_paper_concept.assert_not_called()

def test_generate_openalex_id_uniqueness(openalex_wrapper):
    prefix = "OPENALEX_CONCEPT_"
    identifier1 = "Concept A"
    identifier2 = "Concept B"
    openalex_id1 = openalex_wrapper.generate_openalex_id(prefix, identifier1)
    openalex_id2 = openalex_wrapper.generate_openalex_id(prefix, identifier2)
    assert openalex_id1 != openalex_id2

def test_extract_year(openalex_wrapper):
    assert openalex_wrapper.extract_year(2023) == 2023
    assert openalex_wrapper.extract_year(None) is None
    assert openalex_wrapper.extract_year(999) is None
    assert openalex_wrapper.extract_year(2025) is None

def test_format_author_name(openalex_wrapper):
    author = {"display_name": "John Doe"}
    assert openalex_wrapper.format_author_name(author) == "John Doe"

    author = {"display_name": ""}
    assert openalex_wrapper.format_author_name(author) is None

def test_db_manager_close(openalex_wrapper):
    openalex_wrapper.db_manager.close = MagicMock()
    openalex_wrapper.query_and_store(query="deep learning", max_results=1)
    openalex_wrapper.db_manager.close.assert_called_once()
