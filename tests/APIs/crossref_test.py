import pytest
from unittest.mock import patch, MagicMock
from app.APIs.crossref.crossref_wrapper import api_handler
import requests

@pytest.fixture
def handler():
    return api_handler()

@patch("requests.get")
def test_query_with_results(mock_get, handler):
    # Mock the response from requests.get
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None  # No exception
    mock_response.json.return_value = {
        "message": {
            "items": [
                {"DOI": "10.1000/xyz123", "title": ["Sample Title 1"]},
                {"DOI": "10.1000/xyz124", "title": ["Sample Title 2"]},
            ]
        }
    }
    mock_get.return_value = mock_response

    # Call the query method
    results = list(handler.query("sample query", max_results=2))

    # Verify that the results contain the expected items
    assert len(results) == 2
    assert results[0]["DOI"] == "10.1000/xyz123"
    assert results[0]["title"] == ["Sample Title 1"]
    assert results[1]["DOI"] == "10.1000/xyz124"
    assert results[1]["title"] == ["Sample Title 2"]

@patch("requests.get")
def test_query_no_results(mock_get, handler):
    # Mock the response from requests.get with no items
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None  # No exception
    mock_response.json.return_value = {
        "message": {
            "items": []
        }
    }
    mock_get.return_value = mock_response

    # Call the query method
    results = list(handler.query("sample query", max_results=2))

    # Verify that no results are returned
    assert len(results) == 0

@patch("requests.get")
def test_query_request_exception(mock_get, handler):
    # Mock the requests.get to raise a RequestException
    mock_get.side_effect = requests.exceptions.RequestException("Request failed")

    # Call the query method and verify it handles the exception gracefully
    results = list(handler.query("sample query", max_results=2))
    assert len(results) == 0

@patch("requests.get")
def test_query_with_default_max_results(mock_get, handler):
    # Mock the response from requests.get
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None  # No exception
    mock_response.json.return_value = {
        "message": {
            "items": [
                {"DOI": "10.1000/xyz123", "title": ["Sample Title 1"]}
            ]
        }
    }
    mock_get.return_value = mock_response

    # Call the query method without specifying max_results
    results = list(handler.query("sample query"))

    # Verify that the result contains the expected item
    assert len(results) == 1
    assert results[0]["DOI"] == "10.1000/xyz123"
    assert results[0]["title"] == ["Sample Title 1"]
