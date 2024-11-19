# DatabaseManager.py

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseManager:
    def __init__(self):
        """Initialize the database connection."""
        try:
            self.connection = psycopg2.connect(os.getenv('DATABASE_URL'))
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            print("Database connection established.")
        except psycopg2.Error as e:
            print(f"Error connecting to the database: {e}")
            raise

    def insert_author(
        self,
        openalex_id,
        name,
        first_publication_year=None,
        author_age=None,
        h_index=None,
        delta_h_index=None,
        adopters=None,
        total_papers=None,
        delta_total_papers=None,
        recent_coauthors=None,
        coauthor_pagerank=None,
        total_citations=None,
        citations_per_paper=None,
        max_citations=None,
        total_journals=None
    ):
        """
        Insert or update an author in the database.
        Upsert is based on 'openalex_id'.
        Returns the author's id.
        """
        columns = [
            'openalex_id', 'name', 'first_publication_year', 'author_age',
            'h_index', 'delta_h_index', 'adopters', 'total_papers',
            'delta_total_papers', 'recent_coauthors', 'coauthor_pagerank',
            'total_citations', 'citations_per_paper', 'max_citations',
            'total_journals'
        ]
        values = [
            openalex_id, name, first_publication_year, author_age,
            h_index, delta_h_index, adopters, total_papers,
            delta_total_papers, recent_coauthors, coauthor_pagerank,
            total_citations, citations_per_paper, max_citations,
            total_journals
        ]

        update_columns = [col for col in columns if col != 'openalex_id']

        insert_query = sql.SQL("""
            INSERT INTO authors ({fields})
            VALUES ({placeholders})
            ON CONFLICT (openalex_id)
            DO UPDATE SET
                {updates}
            RETURNING id
        """).format(
            fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns)),
            updates=sql.SQL(', ').join([
                sql.SQL("{field} = CASE WHEN authors.{field} IS NULL AND EXCLUDED.{field} IS NOT NULL THEN EXCLUDED.{field} ELSE authors.{field} END").format(
                    field=sql.Identifier(field)
                ) for field in update_columns
            ])
        )

        try:
            self.cursor.execute(insert_query, values)
            author_id = self.cursor.fetchone()[0]
            print(f"Author '{name}' inserted/updated successfully with ID: {author_id}.")
            return author_id
        except psycopg2.Error as e:
            print(f"Error inserting/updating author '{name}': {e}")
            return None

    def insert_journal(
        self,
        journal_name,
        mean_citations_per_paper=None,
        delta_mean_citations_per_paper=None,
        journal_h_index=None,
        delta_journal_h_index=None,
        max_citations_paper=None,
        total_papers_published=None,
        delta_total_papers_published=None
    ):
        """
        Insert or update a journal in the database.
        Assumes 'journal_name' is unique.
        Returns the journal's id.
        """
        # Check if journal exists based on 'journal_name'
        select_query = sql.SQL("""
            SELECT id FROM journals WHERE journal_name = %s
        """)

        try:
            self.cursor.execute(select_query, (journal_name,))
            result = self.cursor.fetchone()
            if result:
                journal_id = result[0]
                # Update missing fields where necessary
                update_columns = {
                    'mean_citations_per_paper': mean_citations_per_paper,
                    'delta_mean_citations_per_paper': delta_mean_citations_per_paper,
                    'journal_h_index': journal_h_index,
                    'delta_journal_h_index': delta_journal_h_index,
                    'max_citations_paper': max_citations_paper,
                    'total_papers_published': total_papers_published,
                    'delta_total_papers_published': delta_total_papers_published
                }
                # Remove None values to avoid updating with None
                update_columns = {k: v for k, v in update_columns.items() if v is not None}

                if update_columns:
                    set_clause = []
                    update_values = []
                    for field, value in update_columns.items():
                        set_clause.append(
                            sql.SQL("{field} = CASE WHEN journals.{field} IS NULL AND %s IS NOT NULL THEN %s ELSE journals.{field} END").format(
                                field=sql.Identifier(field)
                            )
                        )
                        update_values.extend([value, value])
                    update_query = sql.SQL("""
                        UPDATE journals
                        SET {set_clause}
                        WHERE id = %s
                    """).format(
                        set_clause=sql.SQL(', ').join(set_clause)
                    )
                    update_values.append(journal_id)
                    self.cursor.execute(update_query, update_values)
                    print(f"Journal '{journal_name}' updated successfully with ID: {journal_id}.")
                else:
                    print(f"Journal '{journal_name}' already exists with ID: {journal_id}. No updates performed.")
                return journal_id
            else:
                # Insert new journal
                columns = [
                    'journal_name', 'mean_citations_per_paper', 'delta_mean_citations_per_paper',
                    'journal_h_index', 'delta_journal_h_index', 'max_citations_paper',
                    'total_papers_published', 'delta_total_papers_published'
                ]
                values = [
                    journal_name, mean_citations_per_paper, delta_mean_citations_per_paper,
                    journal_h_index, delta_journal_h_index, max_citations_paper,
                    total_papers_published, delta_total_papers_published
                ]

                insert_query = sql.SQL("""
                    INSERT INTO journals ({fields})
                    VALUES ({placeholders})
                    RETURNING id
                """).format(
                    fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
                    placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns))
                )

                self.cursor.execute(insert_query, values)
                journal_id = self.cursor.fetchone()[0]
                print(f"Journal '{journal_name}' inserted successfully with ID: {journal_id}.")
                return journal_id
        except psycopg2.Error as e:
            print(f"Error inserting/updating journal '{journal_name}': {e}")
            return None

    def insert_paper(
        self,
        openalex_id,
        title,
        abstract=None,
        publication_year=None,
        journal_id=None,
        total_citations=None,
        citations_per_year=None,
        rank_citations_per_year=None,
        pdf_url=None,
        doi=None,
        influential_citations=None,
        delta_citations=None
    ):
        """
        Insert or update a paper in the database.
        Upsert is based on 'doi' if available; otherwise, 'openalex_id'.
        Returns the paper's id.
        """
        # Determine unique key and value
        if doi:
            unique_key = 'doi'
            unique_value = doi
        elif openalex_id:
            unique_key = 'openalex_id'
            unique_value = openalex_id
        else:
            print("Missing both 'doi' and 'openalex_id' in paper_data. Skipping insertion.")
            return None

        columns = [
            'openalex_id', 'title', 'abstract', 'publication_year',
            'journal_id', 'total_citations', 'citations_per_year',
            'rank_citations_per_year', 'pdf_url', 'doi',
            'influential_citations', 'delta_citations'
        ]
        values = [
            openalex_id, title, abstract, publication_year,
            journal_id, total_citations, citations_per_year,
            rank_citations_per_year, pdf_url, doi,
            influential_citations, delta_citations
        ]

        update_columns = [col for col in columns if col != unique_key]

        insert_query = sql.SQL("""
            INSERT INTO papers ({fields})
            VALUES ({placeholders})
            ON CONFLICT ({unique_key})
            DO UPDATE SET
                {updates}
            RETURNING id
        """).format(
            fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns)),
            unique_key=sql.Identifier(unique_key),
            updates=sql.SQL(', ').join([
                sql.SQL("{field} = CASE WHEN papers.{field} IS NULL AND EXCLUDED.{field} IS NOT NULL THEN EXCLUDED.{field} ELSE papers.{field} END").format(
                    field=sql.Identifier(field)
                ) for field in update_columns
            ])
        )

        try:
            self.cursor.execute(insert_query, values)
            paper_id = self.cursor.fetchone()[0]
            print(f"Paper '{title}' inserted/updated successfully with ID: {paper_id}.")
            return paper_id
        except psycopg2.Error as e:
            print(f"Error inserting/updating paper '{title}': {e}")
            return None

    def insert_paper_author(self, paper_id, author_id):
        """
        Insert a paper-author association.
        If the association exists, do nothing.
        """
        if not paper_id or not author_id:
            print("Missing paper_id or author_id in paper_author_data. Skipping insertion.")
            return

        insert_query = sql.SQL("""
            INSERT INTO paper_authors (paper_id, author_id)
            VALUES (%s, %s)
            ON CONFLICT (paper_id, author_id) DO NOTHING
        """)

        try:
            self.cursor.execute(insert_query, (paper_id, author_id))
            print(f"Paper-Author association (Paper ID: {paper_id}, Author ID: {author_id}) inserted successfully.")
        except psycopg2.Error as e:
            print(f"Error inserting Paper-Author association (Paper ID: {paper_id}, Author ID: {author_id}): {e}")

    def insert_citation(
        self,
        paper_id,
        author_id,
        citing_paper_id,
        citation_year=None,
        citation_count=None
    ):
        """
        Insert a citation in the database.
        This function does not perform an upsert because 'id' is the primary key and auto-incremented.
        Returns the citation's id.
        """
        # Remove 'id' if present, as it's auto-generated
        # No action needed since we are using explicit arguments

        # Ensure foreign keys exist
        if not paper_id or not author_id or not citing_paper_id:
            print("Missing paper_id, author_id, or citing_paper_id in citation_data. Skipping insertion.")
            return None

        columns = ['paper_id', 'author_id', 'citing_paper_id', 'citation_year', 'citation_count']
        values = [paper_id, author_id, citing_paper_id, citation_year, citation_count]

        insert_query = sql.SQL("""
            INSERT INTO citations ({fields})
            VALUES ({placeholders})
            RETURNING id
        """).format(
            fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns))
        )

        try:
            self.cursor.execute(insert_query, values)
            inserted_id = self.cursor.fetchone()[0]
            print(f"Citation inserted successfully with ID: {inserted_id}.")
            return inserted_id
        except psycopg2.Error as e:
            print(f"Error inserting citation: {e}")
            return None

    def insert_concept(
        self,
        openalex_id,
        name=None
    ):
        """
        Insert or update a concept in the database.
        Upsert is based on 'openalex_id'.
        Returns the concept's id.
        """
        # Ensure 'openalex_id' is present
        if not openalex_id:
            print("Missing 'openalex_id' in concept_data. Skipping insertion.")
            return None

        columns = ['openalex_id', 'name']
        values = [openalex_id, name]

        update_columns = [col for col in columns if col != 'openalex_id']

        insert_query = sql.SQL("""
            INSERT INTO concepts ({fields})
            VALUES ({placeholders})
            ON CONFLICT (openalex_id)
            DO UPDATE SET
                {updates}
            RETURNING id
        """).format(
            fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns)),
            updates=sql.SQL(', ').join([
                sql.SQL("{field} = CASE WHEN concepts.{field} IS NULL AND EXCLUDED.{field} IS NOT NULL THEN EXCLUDED.{field} ELSE concepts.{field} END").format(
                    field=sql.Identifier(field)
                ) for field in update_columns
            ])
        )

        try:
            self.cursor.execute(insert_query, values)
            concept_id = self.cursor.fetchone()[0]
            print(f"Concept '{name}' inserted/updated successfully with ID: {concept_id}.")
            return concept_id
        except psycopg2.Error as e:
            print(f"Error inserting/updating concept '{name}': {e}")
            return None

    def insert_paper_concept(self, paper_id, concept_id, score=None):
        """
        Insert a paper-concept association.
        If the association exists, update the 'score' if it's missing.
        """
        if not paper_id or not concept_id:
            print("Missing paper_id or concept_id in paper_concept_data. Skipping insertion.")
            return

        # Check if association exists
        select_query = sql.SQL("""
            SELECT score FROM paper_concepts
            WHERE paper_id = %s AND concept_id = %s
        """)
        try:
            self.cursor.execute(select_query, (paper_id, concept_id))
            result = self.cursor.fetchone()
            if result:
                existing_score = result[0]
                if existing_score is None and score is not None:
                    update_query = sql.SQL("""
                        UPDATE paper_concepts
                        SET score = %s
                        WHERE paper_id = %s AND concept_id = %s
                    """)
                    self.cursor.execute(update_query, (score, paper_id, concept_id))
                    print(f"Paper-Concept association (Paper ID: {paper_id}, Concept ID: {concept_id}) updated with score {score}.")
                else:
                    print(f"Paper-Concept association (Paper ID: {paper_id}, Concept ID: {concept_id}) already has a score. Skipping update.")
            else:
                # Insert new association
                insert_query = sql.SQL("""
                    INSERT INTO paper_concepts (paper_id, concept_id, score)
                    VALUES (%s, %s, %s)
                """)
                self.cursor.execute(insert_query, (paper_id, concept_id, score))
                print(f"Paper-Concept association (Paper ID: {paper_id}, Concept ID: {concept_id}) inserted successfully.")
        except psycopg2.Error as e:
            print(f"Error inserting/updating Paper-Concept association (Paper ID: {paper_id}, Concept ID: {concept_id}): {e}")

    def close(self):
        """Close the database connection."""
        try:
            self.cursor.close()
            self.connection.close()
            print("Database connection closed.\n")
        except psycopg2.Error as e:
            print(f"Error closing the database connection: {e}")

if __name__ == "__main__":
    """
    Test the DatabaseManager by inserting sample data.
    """
    db_manager = DatabaseManager()

    try:
        # Insert an author
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

        # Insert a journal
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

        # Insert a paper
        paper_id = db_manager.insert_paper(
            openalex_id='P123456789',
            title='A Comprehensive Study on Testing',
            abstract='This paper explores testing methodologies...',
            publication_year=2021,
            journal_id=journal_id,  # Use the actual journal_id
            total_citations=100,
            citations_per_year=10.0,
            rank_citations_per_year=5,
            pdf_url='http://example.com/paper.pdf',
            doi='10.1234/test.paper.2021',
            influential_citations=20,
            delta_citations=2
        )

        # Insert a paper-author association
        if paper_id and author_id:
            db_manager.insert_paper_author(paper_id, author_id)
        else:
            print("Cannot create Paper-Author association due to missing paper_id or author_id.")

        # Insert a citing paper first to satisfy foreign key constraint
        citing_paper_id = db_manager.insert_paper(
            openalex_id='P987654321',
            title='An Analysis of Testing Techniques',
            abstract='This paper analyzes various testing techniques...',
            publication_year=2022,
            journal_id=journal_id,  # Use the actual journal_id
            total_citations=50,
            citations_per_year=5.0,
            rank_citations_per_year=3,
            pdf_url='http://example.com/citing_paper.pdf',
            doi='10.1234/citing.paper.2022',
            influential_citations=10,
            delta_citations=1
        )

        # Insert a citation
        if paper_id and author_id and citing_paper_id:
            citation_id = db_manager.insert_citation(
                paper_id=paper_id,
                author_id=author_id,
                citing_paper_id=citing_paper_id,
                citation_year=2023,
                citation_count=3
            )
        else:
            print("Cannot insert citation due to missing paper_id, author_id, or citing_paper_id.")

        # Insert a concept
        concept_id = db_manager.insert_concept(
            openalex_id='C123456789',
            name='Testing Methodologies'
        )

        # Insert a paper-concept association
        if paper_id and concept_id:
            db_manager.insert_paper_concept(
                paper_id=paper_id,
                concept_id=concept_id,
                score=0.95
            )
        else:
            print("Cannot create Paper-Concept association due to missing paper_id or concept_id.")

    except Exception as e:
        print(f"An error occurred during testing: {e}")
    finally:
        # Close the database connection
        db_manager.close()
