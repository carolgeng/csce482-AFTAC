import pytest
from unittest.mock import patch, MagicMock
from app.database.DatabaseManager import DatabaseManager
import psycopg2

@pytest.fixture
def db_manager():
    with patch.object(DatabaseManager, "__init__", lambda x: None):
        db_manager = DatabaseManager()
        db_manager.connection = MagicMock()
        db_manager.cursor = MagicMock()
        return db_manager

def test_insert_author(db_manager):
    db_manager.cursor.fetchone.return_value = [1]
    author_id = db_manager.insert_author(
        openalex_id='A123456789',
        name='Jane Doe',
        first_publication_year=2010,
        author_age=40,
        h_index=15,
        delta_h_index=2,
        adopters=100,
        total_papers=50,
        delta_total_papers=5,
        recent_coauthors=10,
        coauthor_pagerank=0.85,
        total_citations=2000,
        citations_per_paper=40.0,
        max_citations=500,
        total_journals=20
    )
    assert author_id == 1
    db_manager.cursor.execute.assert_called_once()

def test_insert_journal(db_manager):
    db_manager.cursor.fetchone.side_effect = [None, [1]]
    journal_id = db_manager.insert_journal(
        journal_name='Journal of Testing',
        mean_citations_per_paper=5.2,
        delta_mean_citations_per_paper=0.3,
        journal_h_index=25,
        delta_journal_h_index=1,
        max_citations_paper=150,
        total_papers_published=300,
        delta_total_papers_published=10
    )
    assert journal_id == 1
    assert db_manager.cursor.execute.call_count == 2

def test_insert_paper(db_manager):
    db_manager.cursor.fetchone.return_value = [1]
    paper_id = db_manager.insert_paper(
        openalex_id='P123456789',
        title='A Comprehensive Study on Testing',
        abstract='This paper explores testing methodologies...',
        publication_year=2021,
        journal_id=1,
        total_citations=100,
        citations_per_year=10.0,
        rank_citations_per_year=5,
        pdf_url='http://example.com/paper.pdf',
        doi='10.1234/test.paper.2021',
        influential_citations=20,
        delta_citations=2
    )
    assert paper_id == 1
    db_manager.cursor.execute.assert_called_once()

def test_insert_paper_author(db_manager):
    db_manager.insert_paper_author(paper_id=1, author_id=1)
    db_manager.cursor.execute.assert_called_once()

def test_insert_citation(db_manager):
    db_manager.cursor.fetchone.return_value = [1]
    citation_id = db_manager.insert_citation(
        paper_id=1,
        author_id=1,
        citing_paper_id=2,
        citation_year=2023,
        citation_count=3
    )
    assert citation_id == 1
    db_manager.cursor.execute.assert_called_once()

def test_insert_concept(db_manager):
    db_manager.cursor.fetchone.return_value = [1]
    concept_id = db_manager.insert_concept(
        openalex_id='C123456789',
        name='Testing Methodologies'
    )
    assert concept_id == 1
    db_manager.cursor.execute.assert_called_once()

def test_insert_paper_concept(db_manager):
    db_manager.cursor.fetchone.return_value = None
    db_manager.insert_paper_concept(paper_id=1, concept_id=1, score=0.95)
    assert db_manager.cursor.execute.call_count == 2

def test_close_connection(db_manager):
    db_manager.close()
    db_manager.cursor.close.assert_called_once()
    db_manager.connection.close.assert_called_once()
