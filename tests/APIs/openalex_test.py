import unittest
from unittest.mock import patch, MagicMock
from app.database.APIs.open_alex.open_alex_wrapper import OpenAlexAPIHandler
import requests

class TestOpenAlexAPIHandler(unittest.TestCase):

    def setUp(self):
        self.api_handler = OpenAlexAPIHandler()

    def test_init(self):
        self.assertIsInstance(self.api_handler, OpenAlexAPIHandler)

    # @patch('app.database.APIs.open_alex.open_alex_wrapper.requests.get')
    # def test_query_success(self, mock_get):
    #     mock_response = MagicMock()
    #     mock_response.json.return_value = {
    #         'results': [{'id': 1}, {'id': 2}],
    #         'meta': {'next_cursor': 'next_page'}
    #     }
    #     mock_get.return_value = mock_response

    #     results = list(self.api_handler.query('test query', max_results=3))

    #     self.assertEqual(len(results), 3)
    #     # self.assertEqual(results[0]['id'], 1)
    #     # self.assertEqual(results[1]['id'], 2)

    #     mock_get.assert_called_with(
    #         'https://api.openalex.org/works',
    #         params={
    #             'search': 'test query',
    #             'per-page': 200,
    #             'cursor': '*',
    #             'sort': 'cited_by_count:desc'
    #         },
    #         headers={'User-Agent': 'YourAppName (your_email@example.com)'},
    #         timeout=30
    #     )

    @patch('app.database.APIs.open_alex.open_alex_wrapper.requests.get')
    def test_query_multiple_pages(self, mock_get):
        mock_responses = [
            MagicMock(json=lambda: {'results': [{'id': 1}, {'id': 2}], 'meta': {'next_cursor': 'next_page'}}),
            MagicMock(json=lambda: {'results': [{'id': 3}], 'meta': {'next_cursor': None}})
        ]
        mock_get.side_effect = mock_responses

        results = list(self.api_handler.query('test query'))

        self.assertEqual(len(results), 3)
        self.assertEqual([r['id'] for r in results], [1, 2, 3])
        self.assertEqual(mock_get.call_count, 2)

    @patch('app.database.APIs.open_alex.open_alex_wrapper.requests.get')
    def test_query_max_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{'id': i} for i in range(1, 6)],
            'meta': {'next_cursor': 'next_page'}
        }
        mock_get.return_value = mock_response

        results = list(self.api_handler.query('test query', max_results=3))

        self.assertEqual(len(results), 3)
        self.assertEqual([r['id'] for r in results], [1, 2, 3])

    @patch('app.database.APIs.open_alex.open_alex_wrapper.requests.get')
    def test_query_no_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': [], 'meta': {'next_cursor': None}}
        mock_get.return_value = mock_response

        results = list(self.api_handler.query('test query'))

        self.assertEqual(len(results), 0)

    @patch('app.database.APIs.open_alex.open_alex_wrapper.requests.get')
    def test_query_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Test error")

        with patch('builtins.print') as mock_print:
            results = list(self.api_handler.query('test query'))

        self.assertEqual(len(results), 0)
        mock_print.assert_called_once_with("An error occurred: Test error")

if __name__ == '__main__':
    unittest.main()