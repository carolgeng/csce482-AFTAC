import pytest
from unittest.mock import MagicMock, patch
from src.APIs.arXiv.arXiv_data import arxiv_api_handler
import arxiv

@patch("src.APIs.arXiv.arXiv_data.arxiv.Client")
def test_query(mock_client):
    # Arrange: Set up the mock to return predefined results
    mock_client_instance = mock_client.return_value
    mock_result = MagicMock()
    mock_result.doi = "10.1234/abcd"
    
    # Mocking the results method to return a list of mock results
    mock_client_instance.results.return_value = [mock_result, mock_result, mock_result]

    handler = arxiv_api_handler()
    max_results = 2
    query = "test query"

    # Act: Call the query method
    results = list(handler.query(query, max_results))

    # Assert: Verify the number of results and that results contain a DOI
    assert len(results) == max_results  # Should only return max_results items
    for result in results:
        assert result.doi is not None
        assert result.doi == "10.1234/abcd"  # Check that DOI matches mock setup
