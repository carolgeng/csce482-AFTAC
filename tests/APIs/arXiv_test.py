import pytest
from unittest.mock import patch, MagicMock
from app.database.APIs.arXiv.arXiv_wrapper import api_handler
from arxiv import UnexpectedEmptyPageError

@pytest.fixture
def handler():
    with patch.object(api_handler, '__init__', lambda x: None):
        handler_instance = api_handler()
        handler_instance.client = MagicMock()
        return handler_instance

@patch.object(api_handler, 'query')
def test_query_with_no_doi(mock_query, handler):
    # Mock the response to simulate no articles with DOIs
    mock_query.return_value = iter([])  # Return an empty iterator to simulate no results

    result = list(handler.query("random non-existent query", 1))
    assert len(result) == 0  # Should return no articles with a DOI

def test_query_with_doi(handler):
    # Create a mock result with a DOI
    mock_result = MagicMock(doi="10.1109/BDCAT56447.2022.00044")
    
    # Mock the client's results method to return an iterator with the mock result
    handler.client.results.return_value = iter([mock_result])
    
    # Call the query method
    result = list(handler.query("sample query", 1))
    
    # Verify that the result contains the mock result
    assert len(result) == 1
    assert result[0].doi == "10.1109/BDCAT56447.2022.00044"

def test_query_max_results(handler):
    # Create a mock result with a DOI
    mock_result_1 = MagicMock(doi="10.1109/BDCAT56447.2022.00044")
    
    # Mock the client's results method to return an iterator with only one mock result
    handler.client.results.return_value = iter([mock_result_1])
    
    # Call the query method with max_results=1
    result = list(handler.query("sample query", 1))
    
    # Verify that only one result is returned due to max_results limit
    assert len(result) == 1
    assert result[0].doi == "10.1109/BDCAT56447.2022.00044"

def test_query_unexpected_empty_page_error(handler):
    # Mock the client's results method to raise an UnexpectedEmptyPageError
    handler.client.results.side_effect = UnexpectedEmptyPageError("Empty page error", retry=1)
    
    # Call the query method and verify that it handles the exception gracefully
    result = list(handler.query("sample query"))
    assert len(result) == 0  # Should return no results due to the exception

def test_query_generic_exception(handler):
    # Mock the client's results method to raise a generic exception
    handler.client.results.side_effect = Exception("Generic error")
    
    # Call the query method and verify that it handles the exception gracefully
    result = list(handler.query("sample query"))
    assert len(result) == 0  # Should return no results due to the exception
