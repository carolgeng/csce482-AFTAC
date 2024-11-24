# import pytest
# from unittest.mock import patch, MagicMock
# from app.database.open_alex_db_wrapper import OpenAlexDbWrapper
# from app.database.DatabaseManager import DatabaseManager
# from app.database.APIs.open_alex.open_alex_wrapper import openalex_api_handler

# @pytest.fixture
# def openalex_wrapper():
#     with patch.object(DatabaseManager, "__init__", lambda x: None), \
#          patch.object(openalex_api_handler, "__init__", lambda x: None):
#         wrapper = OpenAlexDbWrapper()
#         wrapper.db_manager = MagicMock(spec=DatabaseManager)
#         wrapper.api_handler = MagicMock(spec=openalex_api_handler)
#         return wrapper

# def test_generate_openalex_id(openalex_wrapper):
#     prefix = "OPENALEX_AUTHOR_"
#     identifier = "John Doe"
#     openalex_id = openalex_wrapper.generate_openalex_id(prefix, identifier)
#     assert openalex_id.startswith(prefix)
#     assert len(openalex_id) > len(prefix)

# def test_query_and_store_paper(openalex_wrapper):
#     mock_result = {
#         "id": "openalex123",
#         "title": "Sample Paper",
#         "displayed_abstract": "This is a summary of the paper.",
#         "publication_year": 2023,
#         "authorships": [{"author": {"id": "A123", "display_name": "John Doe"}},
#                          {"author": {"id": "A124", "display_name": "Jane Doe"}}],
#         "concepts": [{"id": "C123", "display_name": "Concept1"},
#                       {"id": "C124", "display_name": "Concept2"}],
#         "cited_by_count": 10,
#         "cited_by_influential_count": 2
#     }

#     openalex_wrapper.api_handler.query.return_value = [mock_result]
#     openalex_wrapper.db_manager.insert_paper.return_value = 1
#     openalex_wrapper.db_manager.insert_author.return_value = 2
#     openalex_wrapper.db_manager.insert_concept.return_value = 3
#     openalex_wrapper.db_manager.insert_paper_author.return_value = None
#     openalex_wrapper.db_manager.insert_paper_concept.return_value = None

#     with patch.object(openalex_wrapper.db_manager, 'insert_author', wraps=openalex_wrapper.db_manager.insert_author) as mock_insert_author:
#         with patch.object(openalex_wrapper.db_manager, 'insert_paper_author', wraps=openalex_wrapper.db_manager.insert_paper_author) as mock_insert_paper_author:
#             openalex_wrapper.query_and_store(query="machine learning", max_results=1)
            
#             # Check that the insert methods were called
#             openalex_wrapper.db_manager.insert_paper.assert_called_once()
#             assert mock_insert_author.call_count == len(mock_result['authorships'])
#             assert openalex_wrapper.db_manager.insert_concept.call_count == len(mock_result['concepts'])
#             assert mock_insert_paper_author.call_count == len(mock_result['authorships'])
#             assert openalex_wrapper.db_manager.insert_paper_concept.call_count == len(mock_result['concepts'])

# def test_query_and_store_with_missing_data(openalex_wrapper):
#     mock_result = {
#         "id": "openalex456",  # Provided ID
#         "title": "No Title",  # Default title if missing
#         "displayed_abstract": None,
#         "publication_year": None,  # Missing publication year
#         "authorships": [],  # Missing author data
#         "concepts": []  # No subjects
#     }

#     openalex_wrapper.api_handler.query.return_value = [mock_result]
#     openalex_wrapper.db_manager.insert_paper.return_value = 1  # Paper insertion succeeds even with missing fields

#     openalex_wrapper.query_and_store(query="artificial intelligence", max_results=1)

#     # Check that paper insertion was attempted and succeeded
#     openalex_wrapper.db_manager.insert_paper.assert_called_once()
#     # Author and concept insertion should not be called due to missing data
#     openalex_wrapper.db_manager.insert_author.assert_not_called()
#     openalex_wrapper.db_manager.insert_concept.assert_not_called()
#     openalex_wrapper.db_manager.insert_paper_author.assert_not_called()
#     openalex_wrapper.db_manager.insert_paper_concept.assert_not_called()

# def test_query_and_store_exception_handling(openalex_wrapper):
#     openalex_wrapper.api_handler.query.side_effect = Exception("API Error")

#     openalex_wrapper.query_and_store(query="quantum computing", max_results=1)

#     # Ensure that no inserts were attempted due to the exception
#     openalex_wrapper.db_manager.insert_paper.assert_not_called()
#     openalex_wrapper.db_manager.insert_author.assert_not_called()
#     openalex_wrapper.db_manager.insert_concept.assert_not_called()
#     openalex_wrapper.db_manager.insert_paper_author.assert_not_called()
#     openalex_wrapper.db_manager.insert_paper_concept.assert_not_called()

# def test_generate_openalex_id_uniqueness(openalex_wrapper):
#     prefix = "OPENALEX_CONCEPT_"
#     identifier1 = "Concept A"
#     identifier2 = "Concept B"
#     openalex_id1 = openalex_wrapper.generate_openalex_id(prefix, identifier1)
#     openalex_id2 = openalex_wrapper.generate_openalex_id(prefix, identifier2)
#     assert openalex_id1 != openalex_id2

# def test_extract_year(openalex_wrapper):
#     assert openalex_wrapper.extract_year(2023) == 2023
#     assert openalex_wrapper.extract_year(None) is None
#     assert openalex_wrapper.extract_year(999) is None
#     assert openalex_wrapper.extract_year(2025) is None

# def test_format_author_name(openalex_wrapper):
#     author = {"display_name": "John Doe"}
#     assert openalex_wrapper.format_author_name(author) == "John Doe"

#     author = {"display_name": ""}
#     assert openalex_wrapper.format_author_name(author) is None

# def test_db_manager_close(openalex_wrapper):
#     openalex_wrapper.db_manager.close = MagicMock()
#     openalex_wrapper.query_and_store(query="deep learning", max_results=1)
#     openalex_wrapper.db_manager.close.assert_called_once()

import unittest
from unittest.mock import Mock, patch
from app.database.open_alex_db_wrapper import OpenAlexDbWrapper

class TestOpenAlexDbWrapper(unittest.TestCase):

    @patch('app.database.open_alex_db_wrapper.OpenAlexAPIHandler')
    @patch('app.database.open_alex_db_wrapper.DatabaseManager')
    def setUp(self, mock_db_manager, mock_api_handler):
        self.mock_db_manager = mock_db_manager.return_value
        self.mock_api_handler = mock_api_handler.return_value
        self.wrapper = OpenAlexDbWrapper()

    def test_run_query(self):
        with patch.object(self.wrapper, 'query_and_store') as mock_query_store, \
             patch.object(self.wrapper, 'update_existing_entries') as mock_update:
            self.wrapper.run_query("test query", 10)
            mock_query_store.assert_called_once_with("test query", 10)
            mock_update.assert_called_once()

    @patch('builtins.print')
    def test_query_and_store(self, mock_print):
        mock_result = {
            'id': 'https://openalex.org/W123456789',
            'title': 'Test Paper',
            'abstract_inverted_index': {'test': [0], 'abstract': [1]},
            'publication_year': 2023,
            'doi': '10.1234/test',
            'primary_location': {'pdf_url': 'http://example.com/paper.pdf'},
            'cited_by_count': 5,
            'referenced_works': ['ref1', 'ref2'],
            'authorships': [
                {'author': {'display_name': 'John Doe', 'id': 'A123'}}
            ],
            'concepts': [
                {'display_name': 'Computer Science', 'id': 'C123', 'score': 0.9}
            ]
        }
        self.mock_api_handler.query.return_value = [mock_result]
        self.mock_db_manager.insert_paper.return_value = 1
        self.mock_db_manager.insert_author.return_value = 1
        self.mock_db_manager.insert_concept.return_value = 1

        self.wrapper.query_and_store("test query", 1)

        self.mock_api_handler.query.assert_called_once_with("test query", max_results=1)
        self.mock_db_manager.insert_paper.assert_called_once()
        self.mock_db_manager.insert_author.assert_called_once()
        self.mock_db_manager.insert_paper_author.assert_called_once()
        self.mock_db_manager.insert_concept.assert_called_once()
        self.mock_db_manager.insert_paper_concept.assert_called_once()
        self.mock_db_manager.close.assert_called_once()

    def test_reconstruct_abstract(self):
        abstract_index = {'test': [0], 'abstract': [1]}
        result = self.wrapper.reconstruct_abstract(abstract_index)
        self.assertEqual(result, 'test abstract')

    # def test_reconstruct_abstract_empty(self):
    #     result = self.wrapper.reconstruct_abstract({})
    #     self.assertEqual(result, '')

    def test_reconstruct_abstract_none(self):
        result = self.wrapper.reconstruct_abstract(None)
        self.assertIsNone(result)

    # @patch('app.database.open_alex_db_wrapper.requests.get')
    # def test_update_existing_entries(self, mock_get):
    #     self.mock_db_manager.get_entries_with_placeholders.return_value = [
    #         (1, 'W123', '10.1234/test', 'Test Paper', 2023)
    #     ]
    #     mock_response = Mock()
    #     mock_response.json.return_value = {'id': 'W123', 'title': 'Updated Test Paper'}
    #     mock_get.return_value = mock_response

    #     self.wrapper.update_existing_entries()

    #     self.mock_db_manager.get_entries_with_placeholders.assert_called_once()
    #     mock_get.assert_called_once_with('https://api.openalex.org/works/W123')
    #     self.mock_db_manager.update_paper_entry.assert_called_once_with(1, {'id': 'W123', 'title': 'Updated Test Paper'})

    @patch('app.database.open_alex_db_wrapper.requests.get')
    def test_fetch_openalex_data_doi(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'W123', 'title': 'Test Paper'}
        mock_get.return_value = mock_response

        result = self.wrapper.fetch_openalex_data(None, '10.1234/test', None, None)

        mock_get.assert_called_once_with('https://api.openalex.org/works/doi:10.1234/test')
        self.assertEqual(result, {'id': 'W123', 'title': 'Test Paper'})

    @patch('app.database.open_alex_db_wrapper.requests.get')
    def test_fetch_openalex_data_openalex_id(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'id': 'W123', 'title': 'Test Paper'}
        mock_get.return_value = mock_response

        result = self.wrapper.fetch_openalex_data('W123', None, None, None)

        mock_get.assert_called_once_with('https://api.openalex.org/works/W123')
        self.assertEqual(result, {'id': 'W123', 'title': 'Test Paper'})

    @patch('app.database.open_alex_db_wrapper.requests.get')
    def test_fetch_openalex_data_title_year(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'results': [{'id': 'W123', 'title': 'Test Paper'}]}
        mock_get.return_value = mock_response

        result = self.wrapper.fetch_openalex_data(None, None, 'Test Paper', 2023)

        mock_get.assert_called_once_with('https://api.openalex.org/works?filter=title.search:Test+Paper AND publication_year:2023')
        self.assertEqual(result, {'id': 'W123', 'title': 'Test Paper'})

    @patch('app.database.open_alex_db_wrapper.requests.get')
    def test_fetch_openalex_data_no_match(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'results': []}
        mock_get.return_value = mock_response

        result = self.wrapper.fetch_openalex_data(None, None, 'Test Paper', 2023)

        self.assertIsNone(result)

    # @patch('app.database.open_alex_db_wrapper.requests.get')
    # def test_fetch_openalex_data_error(self, mock_get):
    #     mock_get.side_effect = Exception("API Error")

    #     result = self.wrapper.fetch_openalex_data('W123', None, None, None)

    #     self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()