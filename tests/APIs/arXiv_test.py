import pytest
from unittest.mock import patch
from app.APIs.arXiv.arXiv_wrapper import api_handler

@pytest.fixture
def handler():
    return api_handler()

@patch.object(api_handler, 'query')
def test_query_with_no_doi(mock_query, handler):
    # Mock the response to simulate no articles with DOIs
    mock_query.return_value = iter([])  # Return an empty iterator to simulate no results

    result = handler.query("random non-existent query", 1)
    assert len(list(result)) == 0  # Should return no articles with a DOI
