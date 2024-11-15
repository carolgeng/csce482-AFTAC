import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection details
DATABASE_URL = os.getenv("DATABASE_URL")

# Database Manager class
class DatabaseManager:
    def __init__(self):
        self.connection = psycopg2.connect(DATABASE_URL)
        self.cursor = self.connection.cursor()

    def close_connection(self):
        self.cursor.close()
        self.connection.close()

    def get_paper_by_doi(self, doi):
        query = sql.SQL("""
            SELECT * FROM papers WHERE doi = %s
        """)
        self.cursor.execute(query, (doi,))
        return self.cursor.fetchone()

    def insert_paper(self, openalex_id, title, abstract, publication_year, journal_id, total_citations, citations_per_year,
                     rank_citations_per_year, pdf_url, doi, influential_citations, delta_citations):
        query = sql.SQL("""
            INSERT INTO papers (openalex_id, title, abstract, publication_year, journal_id, total_citations, citations_per_year,
                                rank_citations_per_year, pdf_url, doi, influential_citations, delta_citations)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """)
        self.cursor.execute(query, (openalex_id, title, abstract, publication_year, journal_id, total_citations, citations_per_year,
                                    rank_citations_per_year, pdf_url, doi, influential_citations, delta_citations))
        self.connection.commit()

    def update_paper_if_missing(self, existing_paper_id, openalex_id, title, abstract, publication_year, pdf_url, doi):
        query = sql.SQL("""
            UPDATE papers
            SET openalex_id = COALESCE(%s, openalex_id),
                title = COALESCE(%s, title),
                abstract = COALESCE(%s, abstract),
                publication_year = COALESCE(%s, publication_year),
                pdf_url = COALESCE(%s, pdf_url),
                doi = COALESCE(%s, doi)
            WHERE id = %s
        """)
        self.cursor.execute(query, (openalex_id, title, abstract, publication_year, pdf_url, doi, existing_paper_id))
        self.connection.commit()

    def insert_author(self, openalex_id, name, first_publication_year, author_age, h_index, delta_h_index, adopters,
                      total_papers, delta_total_papers, recent_coauthors, coauthor_pagerank, total_citations,
                      citations_per_paper, max_citations, total_journals, mean_journal_citations_per_paper):
        query = sql.SQL("""
            INSERT INTO authors (openalex_id, name, first_publication_year, author_age, h_index, delta_h_index, adopters,
                                total_papers, delta_total_papers, recent_coauthors, coauthor_pagerank, total_citations,
                                citations_per_paper, max_citations, total_journals, mean_journal_citations_per_paper)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """)
        self.cursor.execute(query, (openalex_id, name, first_publication_year, author_age, h_index, delta_h_index, adopters,
                                    total_papers, delta_total_papers, recent_coauthors, coauthor_pagerank, total_citations,
                                    citations_per_paper, max_citations, total_journals, mean_journal_citations_per_paper))
        self.connection.commit()

    def get_or_create_author(self, openalex_id, name, first_publication_year, author_age, h_index, delta_h_index, adopters,
                             total_papers, delta_total_papers, recent_coauthors, coauthor_pagerank, total_citations,
                             citations_per_paper, max_citations, total_journals, mean_journal_citations_per_paper):
        query = sql.SQL("""
            SELECT * FROM authors WHERE name = %s
        """)
        self.cursor.execute(query, (name,))
        author = self.cursor.fetchone()

        if author:
            return author[0]  # Assuming the ID is the first column
        else:
            self.insert_author(openalex_id, name, first_publication_year, author_age, h_index, delta_h_index, adopters,
                               total_papers, delta_total_papers, recent_coauthors, coauthor_pagerank, total_citations,
                               citations_per_paper, max_citations, total_journals, mean_journal_citations_per_paper)
            return self.cursor.lastrowid

    def insert_or_ignore_paper_author(self, paper_id, author_id):
        query = sql.SQL("""
            INSERT INTO paper_authors (paper_id, author_id)
            VALUES (%s, %s)
            ON CONFLICT (paper_id, author_id) DO NOTHING
        """)
        self.cursor.execute(query, (paper_id, author_id))
        self.connection.commit()

    def insert_concept(self, openalex_id, name):
        query = sql.SQL("""
            INSERT INTO concepts (openalex_id, name)
            VALUES (%s, %s)
            ON CONFLICT (openalex_id) DO NOTHING
        """)
        self.cursor.execute(query, (openalex_id, name))
        self.connection.commit()

    def insert_paper_concept(self, paper_id, concept_id, score):
        query = sql.SQL("""
            INSERT INTO paper_concepts (paper_id, concept_id, score)
            VALUES (%s, %s, %s)
            ON CONFLICT (paper_id, concept_id) DO NOTHING
        """)
        self.cursor.execute(query, (paper_id, concept_id, score))
        self.connection.commit()

if __name__ == "__main__":
    db_manager = DatabaseManager()
    try:
        # Example usage:
        db_manager.insert_author("authsf123", "Johnie Doe", 2000, 45, 20, 2, 10, 50, 5, 30, 0.7, 1000, 20.0, 300, 15, 10.5)
    finally:
        db_manager.close_connection()
