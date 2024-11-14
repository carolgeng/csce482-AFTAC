import sqlite3

class DatabaseManager:
    def __init__(self, db_file='data.db'):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def insert_author(self, name, first_publication_year=None, author_age=None, h_index=0,
                      delta_h_index=None, adopters=0, total_papers=0, delta_total_papers=None,
                      recent_coauthors=None, coauthor_pagerank=0.0, total_citations=0):
        sql = '''
        INSERT INTO authors (name, first_publication_year, author_age, h_index, delta_h_index, adopters,
                             total_papers, delta_total_papers, recent_coauthors, coauthor_pagerank, total_citations)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        values = (name, first_publication_year, author_age, h_index, delta_h_index, adopters,
                  total_papers, delta_total_papers, recent_coauthors, coauthor_pagerank, total_citations)
        self.cursor.execute(sql, values)
        self.connection.commit()
        return self.cursor.lastrowid

    def insert_journal(self, journal_name, mean_citations_per_paper=0.0, delta_mean_citations_per_paper=None,
                       journal_h_index=0, delta_journal_h_index=None, max_citations_paper=None,
                       total_papers_published=0, delta_total_papers_published=None):
        sql = '''
        INSERT INTO journals (journal_name, mean_citations_per_paper, delta_mean_citations_per_paper,
                              journal_h_index, delta_journal_h_index, max_citations_paper,
                              total_papers_published, delta_total_papers_published)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        values = (journal_name, mean_citations_per_paper, delta_mean_citations_per_paper,
                  journal_h_index, delta_journal_h_index, max_citations_paper,
                  total_papers_published, delta_total_papers_published)
        self.cursor.execute(sql, values)
        self.connection.commit()
        return self.cursor.lastrowid

    def insert_paper(self, corpus_id, title, abstract=None, publication_year=None, journal_id=None,
                     total_citations=0, influential_citations=0, delta_citations=0, citations_per_year=0.0,
                     rank_citations_per_year=None, pdf_url=None, doi=None):
        sql = '''
        INSERT INTO papers (title, abstract, publication_year, journal_id, total_citations,
                            influential_citations, delta_citations, citations_per_year,
                            rank_citations_per_year, pdf_url, doi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        values = (title, abstract, publication_year, journal_id, total_citations,
                  influential_citations, delta_citations, citations_per_year,
                  rank_citations_per_year, pdf_url, doi)
        self.cursor.execute(sql, values)
        self.connection.commit()
        return self.cursor.lastrowid

    def insert_paper_author(self, paper_id, author_id):
        sql = '''
        INSERT INTO paper_authors (paper_id, author_id)
        VALUES (?, ?)
        '''
        values = (paper_id, author_id)
        self.cursor.execute(sql, values)
        self.connection.commit()

    def close_connection(self):
        self.connection.close()

    def get_or_create_author(self, name, **kwargs):
        sql = "SELECT id FROM authors WHERE name = ?"
        self.cursor.execute(sql, (name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            return self.insert_author(name, **kwargs)

    def get_or_create_journal(self, journal_name, **kwargs):
        sql = "SELECT id FROM journals WHERE journal_name = ?"
        self.cursor.execute(sql, (journal_name,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            return self.insert_journal(journal_name, **kwargs)
