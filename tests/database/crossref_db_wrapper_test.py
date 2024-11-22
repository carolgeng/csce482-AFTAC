import pytest
from unittest.mock import patch, MagicMock
from app.database.crossref_db_wrapper import CrossRefDbWrapper
from app.database.DatabaseManager import DatabaseManager
from app.database.APIs.crossref.crossref_wrapper import api_handler

@pytest.fixture
def crossref_wrapper():
    with patch.object(DatabaseManager, "__init__", lambda x: None), \
         patch.object(api_handler, "__init__", lambda x: None):
        wrapper = CrossRefDbWrapper()
        wrapper.db_manager = MagicMock(spec=DatabaseManager)
        wrapper.api_handler = MagicMock(spec=api_handler)
        return wrapper

def test_generate_openalex_id(crossref_wrapper):
    prefix = "CROSSREF_AUTHOR_"
    identifier = "John Doe"
    openalex_id = crossref_wrapper.generate_openalex_id(prefix, identifier)
    assert openalex_id.startswith(prefix)
    assert len(openalex_id) > len(prefix)

def test_query_and_store_paper(crossref_wrapper):
    mock_result = {
        "DOI": "10.1234/crossref.123",
        "title": ["Sample Paper"],
        "abstract": "This is a summary of the paper.",
        "published": {"date-parts": [[2023]]},
        "link": [{"content-type": "application/pdf", "URL": "http://example.com/paper.pdf"}],
        "author": [{"given": "John", "family": "Doe"}, {"given": "Jane", "family": "Doe"}],
        "subject": ["Category1", "Category2"]
    }

    crossref_wrapper.api_handler.query.return_value = [mock_result]
    crossref_wrapper.db_manager.insert_paper.return_value = 1
    crossref_wrapper.db_manager.insert_author.return_value = 2
    crossref_wrapper.db_manager.insert_concept.return_value = 3
    crossref_wrapper.db_manager.insert_paper_author.return_value = None
    crossref_wrapper.db_manager.insert_paper_concept.return_value = None

    with patch.object(crossref_wrapper.db_manager, 'insert_author', wraps=crossref_wrapper.db_manager.insert_author) as mock_insert_author:
        with patch.object(crossref_wrapper.db_manager, 'insert_paper_author', wraps=crossref_wrapper.db_manager.insert_paper_author) as mock_insert_paper_author:
            crossref_wrapper.query_and_store(query="machine learning", max_results=1)
            
            # Check that the insert methods were called
            crossref_wrapper.db_manager.insert_paper.assert_called_once()
            assert mock_insert_author.call_count == len(mock_result['author'])
            assert crossref_wrapper.db_manager.insert_concept.call_count == len(mock_result['subject'])
            assert mock_insert_paper_author.call_count == len(mock_result['author'])
            assert crossref_wrapper.db_manager.insert_paper_concept.call_count == len(mock_result['subject'])

# def test_query_and_store_with_missing_data(crossref_wrapper):
#     mock_result = {
#         "DOI": "10.1234/crossref.456",  # Provided DOI
#         "title": ["No Title"],  # Default title if missing
#         "abstract": None,
#         "published": None,  # Missing publication year
#         "link": [],
#         "author": [],  # Missing author data
#         "subject": []  # No subjects
#     }

#     crossref_wrapper.api_handler.query.return_value = [mock_result]
#     crossref_wrapper.db_manager.insert_paper.return_value = 1  # Paper insertion succeeds even with missing fields

#     with patch.object(crossref_wrapper, 'extract_year', return_value=None):
#         crossref_wrapper.query_and_store(query="artificial intelligence", max_results=1)

#     # Check that paper insertion was attempted and succeeded
#     crossref_wrapper.db_manager.insert_paper.assert_called_once()
#     # Author and concept insertion should not be called due to missing data
#     crossref_wrapper.db_manager.insert_author.assert_not_called()
#     crossref_wrapper.db_manager.insert_concept.assert_not_called()
#     crossref_wrapper.db_manager.insert_paper_author.assert_not_called()
#     crossref_wrapper.db_manager.insert_paper_concept.assert_not_called()

def test_query_and_store_exception_handling(crossref_wrapper):
    crossref_wrapper.api_handler.query.side_effect = Exception("API Error")

    crossref_wrapper.query_and_store(query="quantum computing", max_results=1)

    # Ensure that no inserts were attempted due to the exception
    crossref_wrapper.db_manager.insert_paper.assert_not_called()
    crossref_wrapper.db_manager.insert_author.assert_not_called()
    crossref_wrapper.db_manager.insert_concept.assert_not_called()
    crossref_wrapper.db_manager.insert_paper_author.assert_not_called()
    crossref_wrapper.db_manager.insert_paper_concept.assert_not_called()

def test_generate_openalex_id_uniqueness(crossref_wrapper):
    prefix = "CROSSREF_CONCEPT_"
    identifier1 = "Concept A"
    identifier2 = "Concept B"
    openalex_id1 = crossref_wrapper.generate_openalex_id(prefix, identifier1)
    openalex_id2 = crossref_wrapper.generate_openalex_id(prefix, identifier2)
    assert openalex_id1 != openalex_id2

def test_extract_year(crossref_wrapper):
    assert crossref_wrapper.extract_year([2023]) == 2023
    assert crossref_wrapper.extract_year(2023) == 2023
    assert crossref_wrapper.extract_year(None) is None
    assert crossref_wrapper.extract_year([]) is None

def test_extract_pdf_url(crossref_wrapper):
    links = [
        {"content-type": "application/pdf", "URL": "http://example.com/paper.pdf"},
        {"content-type": "text/html", "URL": "http://example.com/paper.html"}
    ]
    assert crossref_wrapper.extract_pdf_url(links) == "http://example.com/paper.pdf"
    assert crossref_wrapper.extract_pdf_url([]) is None

def test_format_author_name(crossref_wrapper):
    author = {"given": "John", "family": "Doe"}
    assert crossref_wrapper.format_author_name(author) == "John Doe"

    author = {"given": "", "family": "Doe"}
    assert crossref_wrapper.format_author_name(author) == "Doe"

    author = {"given": "John", "family": ""}
    assert crossref_wrapper.format_author_name(author) == "John"

    author = {"given": "", "family": ""}
    assert crossref_wrapper.format_author_name(author) is None

def test_db_manager_close(crossref_wrapper):
    crossref_wrapper.db_manager.close = MagicMock()
    crossref_wrapper.query_and_store(query="deep learning", max_results=1)
    crossref_wrapper.db_manager.close.assert_called_once()
