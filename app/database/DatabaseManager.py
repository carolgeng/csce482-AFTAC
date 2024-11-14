import sqlite3

class DatabaseManager:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.connection.row_factory = sqlite3.Row  # This enables dictionary-like access to row data
        self.cursor = self.connection.cursor()

    def close_connection(self):
        self.connection.close()

    def get_or_create_journal(self, journal_name, mean_citations_per_paper, delta_mean_citations_per_paper, journal_h_index, delta_journal_h_index, max_citations_paper, total_papers_published, delta_total_papers_published):
        # Check if the journal already exists
        self.cursor.execute("SELECT id FROM journals WHERE journal_name = ?", (journal_name,))
        row = self.cursor.fetchone()
        if row:
            return row['id']
        else:
            # Insert the new journal
            self.cursor.execute("""
                INSERT INTO journals (
                    journal_name,
                    mean_citations_per_paper,
                    delta_mean_citations_per_paper,
                    journal_h_index,
                    delta_journal_h_index,
                    max_citations_paper,
                    total_papers_published,
                    delta_total_papers_published
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                journal_name,
                mean_citations_per_paper,
                delta_mean_citations_per_paper,
                journal_h_index,
                delta_journal_h_index,
                max_citations_paper,
                total_papers_published,
                delta_total_papers_published
            ))
            self.connection.commit()
            return self.cursor.lastrowid

    def insert_paper(self, corpus_id, title, abstract, publication_year, journal_id, total_citations, influential_citations, delta_citations, citations_per_year, rank_citations_per_year, pdf_url, doi):
        # Insert the new paper
        sql = """
            INSERT INTO papers (
                openalex_id,
                title,
                abstract,
                publication_year,
                journal_id,
                total_citations,
                citations_per_year,
                rank_citations_per_year,
                pdf_url,
                doi,
                influential_citations,
                delta_citations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            corpus_id,
            title,
            abstract,
            publication_year,
            journal_id,
            total_citations,
            citations_per_year,
            rank_citations_per_year,
            pdf_url,
            doi,
            influential_citations,
            delta_citations
        )
        self.cursor.execute(sql, values)
        self.connection.commit()
        return self.cursor.lastrowid

    def get_or_create_author(self, name, first_publication_year, author_age, h_index, delta_h_index, adopters, total_papers, delta_total_papers, recent_coauthors, coauthor_pagerank, total_citations):
        # Check if the author already exists
        self.cursor.execute("SELECT id FROM authors WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        if row:
            return row['id']
        else:
            # Insert the new author
            self.cursor.execute("""
                INSERT INTO authors (
                    openalex_id,
                    name,
                    first_publication_year,
                    author_age,
                    h_index,
                    delta_h_index,
                    adopters,
                    total_papers,
                    delta_total_papers,
                    recent_coauthors,
                    coauthor_pagerank,
                    total_citations,
                    citations_per_paper,
                    max_citations,
                    total_journals,
                    mean_journal_citations_per_paper
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                None,  # openalex_id can be None for now
                name,
                first_publication_year,
                author_age,
                h_index,
                delta_h_index,
                adopters,
                total_papers,
                delta_total_papers,
                recent_coauthors,
                coauthor_pagerank,
                total_citations,
                0.0,   # citations_per_paper
                0,     # max_citations
                0,     # total_journals
                0.0    # mean_journal_citations_per_paper
            ))
            self.connection.commit()
            return self.cursor.lastrowid

    def insert_or_ignore_paper_author(self, paper_id, author_id):
        # Insert the association into the paper_authors table or ignore if it already exists
        sql = """
            INSERT OR IGNORE INTO paper_authors (paper_id, author_id) VALUES (?, ?)
        """
        self.cursor.execute(sql, (paper_id, author_id))
        self.connection.commit()

    def get_paper_by_doi(self, doi):
        # Returns the row of the paper with the given DOI, or None if it doesn't exist
        if not doi:
            return None
        self.cursor.execute("SELECT * FROM papers WHERE doi = ?", (doi,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
