import sqlite3

class DBAccess:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def insert_paper(
            self,
            title,
            abstract,
            publication_year,
            journal_id=None,
            total_citations=None,
            max_citations=None,
            citations_per_year=None,
            rank_citations_per_year=None,
            pdf_url=None,
            doi=None):
        # Connect to the SQLite database
        conn = sqlite3.connect(self.filepath)
        cursor = conn.cursor()

        # Insert new paper
        cursor.execute('''
        INSERT INTO papers (title, abstract, publication_year, journal_id, total_citations, max_citations, 
                           citations_per_year, rank_citations_per_year, pdf_url, doi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, abstract, publication_year, journal_id, total_citations, max_citations, 
              citations_per_year, rank_citations_per_year, pdf_url, doi))
        
        # Commit changes and close the connection
        conn.commit()
        conn.close()
        print("Paper inserted successfully.")