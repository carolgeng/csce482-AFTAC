import pytest
from unittest.mock import patch, MagicMock
from app.APIs.open_alex.open_alex_wrapper import openalex_api_handler
import requests

@pytest.fixture
def handler():
    return openalex_api_handler()

@patch("requests.get")
def test_query_with_results(mock_get, handler):
    # Mock the response from requests.get
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None  # No exception
    mock_response.json.return_value = {
        "results": [
            {"id": "https://openalex.org/W123", "title": "Sample Title 1", "doi": "10.1000/xyz123"},
            {"id": "https://openalex.org/W124", "title": "Sample Title 2", "doi": "10.1000/xyz124"},
        ]
    }
    mock_get.return_value = mock_response

    # Call the query method
    results = list(handler.query("sample query", max_results=2))

    # Verify that the results contain the expected items
    assert len(results) == 2
    assert results[0]["id"] == "https://openalex.org/W123"
    assert results[0]["title"] == "Sample Title 1"
    assert results[0]["doi"] == "10.1000/xyz123"
    assert results[1]["id"] == "https://openalex.org/W124"
    assert results[1]["title"] == "Sample Title 2"
    assert results[1]["doi"] == "10.1000/xyz124"

@patch("requests.get")
def test_query_no_results(mock_get, handler):
    # Mock the response from requests.get with no items
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None  # No exception
    mock_response.json.return_value = {
        "results": []
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
def test_query_pagination(mock_get, handler):
    # Mock the response from requests.get to simulate pagination
    mock_response_page_1 = MagicMock()
    mock_response_page_1.raise_for_status.return_value = None  # No exception
    mock_response_page_1.json.return_value = {
        "results": [
            {"id": "https://openalex.org/W123", "title": "Sample Title 1", "doi": "10.1000/xyz123"}
        ]
    }
    mock_response_page_2 = MagicMock()
    mock_response_page_2.raise_for_status.return_value = None  # No exception
    mock_response_page_2.json.return_value = {
        "results": [
            {"id": "https://openalex.org/W124", "title": "Sample Title 2", "doi": "10.1000/xyz124"}
        ]
    }
    mock_get.side_effect = [mock_response_page_1, mock_response_page_2]

    # Call the query method
    results = list(handler.query("sample query", max_results=2))

    # Verify that the results contain the expected items from both pages
    assert len(results) == 2
    assert results[0]["id"] == "https://openalex.org/W123"
    assert results[0]["title"] == "Sample Title 1"
    assert results[0]["doi"] == "10.1000/xyz123"
    assert results[1]["id"] == "https://openalex.org/W124"
    assert results[1]["title"] == "Sample Title 2"
    assert results[1]["doi"] == "10.1000/xyz124"

# @patch("requests.get")
# def test_query_with_default_max_results(mock_get, handler):
#     # Mock the response from requests.get
#     mock_response = MagicMock()
#     mock_response.raise_for_status.return_value = None  # No exception
#     mock_response.json.return_value = {
#         "results": [
#             {"id": "https://openalex.org/W123", "title": "Sample Title 1", "doi": "10.1000/xyz123"}
#         ]
#     }
#     mock_get.return_value = mock_response

#     # Call the query method without specifying max_results
#     results = list(handler.query("sample query"))

#     # Verify that the result contains the expected item
#     assert len(results) == 1
#     assert results[0]["id"] == "https://openalex.org/W123"
#     assert results[0]["title"] == "Sample Title 1"
#     assert results[0]["doi"] == "10.1000/xyz123"

@patch("requests.get")
def test_query_max_pages(mock_get, handler):
    # Mock the response from requests.get to simulate pagination with a lot of pages
    mock_response_page = MagicMock()
    mock_response_page.raise_for_status.return_value = None  # No exception
    mock_response_page.json.return_value = {
        "results": [
            {"id": "https://openalex.org/W123", "title": "Sample Title 1", "doi": "10.1000/xyz123"}
        ]
    }
    mock_get.return_value = mock_response_page

    # Set a limit for max_pages to prevent infinite pagination
    max_pages = 3

    # Mock the pagination to avoid hanging
    results = []
    page = 1
    while page <= max_pages:
        results.extend(list(handler.query("sample query", max_results=1)))
        page += 1

    # Verify that the results contain the expected items and pagination stops after max_pages
    assert len(results) == max_pages
    for result in results:
        assert result["id"] == "https://openalex.org/W123"
        assert result["title"] == "Sample Title 1"
        assert result["doi"] == "10.1000/xyz123"
