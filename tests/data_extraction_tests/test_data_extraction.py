import pytest
from unittest.mock import patch, MagicMock
import os
from src.data_extraction.app import download_s2orc_dataset, save_paper_to_db


@patch('src.data_extraction.app.requests.get')
@patch('src.data_extraction.app.wget.download')
@patch('src.data_extraction.app.gzip.open')
def test_download_s2orc_dataset(mock_gzip_open, mock_wget_download, mock_requests_get):
    # Mock the API response for the release ID
    mock_requests_get.side_effect = [
        MagicMock(json=lambda: {"release_id": "latest_release_id"}),
        MagicMock(json=lambda: {"files": [
            "https://ai2-s2ag.s3.amazonaws.com/staging/shard_id/s2orc/shard.gz"
        ]})
    ]

    # Mock gzip file reading
    mock_gzip_open.return_value.__enter__.return_value = [
        b'{"content": {"text": "sample text", "annotations": {"title": [{"start": 0, "end": 11}], "abstract": [{"start": 12, "end": 20}]}}}'
    ]

    # Run the function
    download_s2orc_dataset()

    # Construct the expected output path
    expected_out_path = os.path.abspath("shard.gz")

    # Verify the download call by inspecting the arguments
    mock_wget_download.assert_called_once()
    call_args = mock_wget_download.call_args
    assert call_args[0][0] == "https://ai2-s2ag.s3.amazonaws.com/staging/shard_id/s2orc/shard.gz"
    assert call_args[1]['out'].endswith("shard.gz")

    # Assert that gzip was opened to read the downloaded file
    mock_gzip_open.assert_called_once_with(expected_out_path, 'rb')
