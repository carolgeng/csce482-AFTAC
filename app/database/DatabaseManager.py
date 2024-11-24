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

    def insert_author(self, openalex_id, name, **kwargs):
        """
        Insert or update an author in the database.
        Upsert is based on 'openalex_id'.
        Only updates fields that are null or placeholders.
        Returns the author's id.
        """
        columns = ['openalex_id', 'name'] + list(kwargs.keys())
        values = [openalex_id, name] + list(kwargs.values())

        update_columns = [col for col in columns if col != 'openalex_id']

        # Define which fields are strings
        string_fields = ['openalex_id', 'name']

        update_statements = []
        for field in update_columns:
            if field in string_fields:
                condition = sql.SQL("authors.{field} IS NULL OR authors.{field} = ''").format(
                    field=sql.Identifier(field)
                )
            else:
                condition = sql.SQL("authors.{field} IS NULL OR authors.{field} = 0").format(
                    field=sql.Identifier(field)
                )
            update_statement = sql.SQL("{field} = CASE WHEN {condition} THEN EXCLUDED.{field} ELSE authors.{field} END").format(
                field=sql.Identifier(field),
                condition=condition
            )
            update_statements.append(update_statement)

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
            updates=sql.SQL(', ').join(update_statements)
        )

        try:
            self.cursor.execute(insert_query, values)
            author_id = self.cursor.fetchone()[0]
            print(f"Author '{name}' inserted/updated successfully with ID: {author_id}.")
            return author_id
        except psycopg2.Error as e:
            print(f"Error inserting/updating author '{name}': {e}")
            return None


    def insert_journal(self, journal_name, **kwargs):
        """
        Insert or update a journal in the database.
        Assumes 'journal_name' is unique.
        Only updates fields that are null or placeholders.
        Returns the journal's id.
        """
        columns = ['journal_name'] + list(kwargs.keys())
        values = [journal_name] + list(kwargs.values())

        update_columns = [col for col in columns if col != 'journal_name']

        insert_query = sql.SQL("""
            INSERT INTO journals ({fields})
            VALUES ({placeholders})
            ON CONFLICT (journal_name)
            DO UPDATE SET
                {updates}
            RETURNING id
        """).format(
            fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(', ').join(sql.Placeholder() * len(columns)),
            updates=sql.SQL(', ').join([
                sql.SQL("{field} = CASE WHEN journals.{field} IS NULL OR journals.{field} = 0 THEN EXCLUDED.{field} ELSE journals.{field} END").format(
                    field=sql.Identifier(field)
                ) for field in update_columns
            ])
        )

        try:
            self.cursor.execute(insert_query, values)
            journal_id = self.cursor.fetchone()[0]
            print(f"Journal '{journal_name}' inserted/updated successfully with ID: {journal_id}.")
            return journal_id
        except psycopg2.Error as e:
            print(f"Error inserting/updating journal '{journal_name}': {e}")
            return None

    def insert_paper(self, openalex_id, title, **kwargs):
        """
        Insert or update a paper in the database.
        Upsert is based on 'doi' if available and non-empty; otherwise, 'openalex_id' if available and non-empty.
        If neither is available, skip inserting the paper.
        Only updates fields that are null or placeholders.
        Returns the paper's id.
        """
        doi = kwargs.get('doi')
        doi = doi.strip() if doi else None

        openalex_id = openalex_id.strip() if openalex_id else None

        if doi:
            unique_key = 'doi'
            unique_value = doi
        elif openalex_id:
            unique_key = 'openalex_id'
            unique_value = openalex_id
        else:
            # Neither DOI nor OpenAlex ID is available
            print(f"Cannot insert/update paper '{title}' without 'doi' or 'openalex_id'. Skipping.")
            return None

        columns = ['openalex_id', 'title'] + list(kwargs.keys())
        values = [openalex_id, title] + list(kwargs.values())

        update_columns = [col for col in columns if col != unique_key]

        # Define which fields are strings
        string_fields = ['openalex_id', 'title', 'abstract', 'pdf_url', 'doi']

        update_statements = []
        for field in update_columns:
            if field in string_fields:
                condition = sql.SQL("papers.{field} IS NULL OR papers.{field} = ''").format(
                    field=sql.Identifier(field)
                )
            else:
                condition = sql.SQL("papers.{field} IS NULL OR papers.{field} = 0").format(
                    field=sql.Identifier(field)
                )
            update_statement = sql.SQL("{field} = CASE WHEN {condition} THEN EXCLUDED.{field} ELSE papers.{field} END").format(
                field=sql.Identifier(field),
                condition=condition
            )
            update_statements.append(update_statement)

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
            updates=sql.SQL(', ').join(update_statements)
        )

        try:
            self.cursor.execute(insert_query, values)
            paper_id = self.cursor.fetchone()[0]
            print(f"Paper '{title}' inserted/updated successfully with ID: {paper_id}.")
            return paper_id
        except psycopg2.Error as e:
            print(f"Error inserting/updating paper '{title}': {e}")
            return None


    def insert_concept(self, openalex_id, name, **kwargs):
        """
        Insert or update a concept in the database.
        Upsert is based on 'openalex_id'.
        Only updates fields that are null or placeholders.
        Returns the concept's id.
        """
        columns = ['openalex_id', 'name'] + list(kwargs.keys())
        values = [openalex_id, name] + list(kwargs.values())

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
                sql.SQL("{field} = CASE WHEN concepts.{field} IS NULL THEN EXCLUDED.{field} ELSE concepts.{field} END").format(
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
                if (existing_score is None or existing_score == 0) and score:
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

    def insert_citation(self, paper_id, author_id, citing_paper_id, citation_year=None, citation_count=None):
        """
        Insert a citation in the database.
        This function does not perform an upsert because 'id' is the primary key and auto-incremented.
        Returns the citation's id.
        """
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
            citation_id = self.cursor.fetchone()[0]
            print(f"Citation inserted successfully with ID: {citation_id}.")
            return citation_id
        except psycopg2.Error as e:
            print(f"Error inserting citation: {e}")
            return None

    def get_entries_with_placeholders(self):
        """
        Fetch entries from the database that have placeholder zeros or nulls.
        Currently checks for papers with total_citations as NULL or 0.
        Modify this method to include other fields and tables as needed.
        """
        try:
            self.cursor.execute("""
                SELECT id, openalex_id, doi, title, publication_year FROM papers
                WHERE total_citations IS NULL OR total_citations = 0
            """)
            entries = self.cursor.fetchall()
            return entries
        except psycopg2.Error as e:
            print(f"Error fetching entries with placeholders: {e}")
            return []

    def update_paper_entry(self, paper_id, openalex_data):
        """
        Update a paper entry in the database with data from OpenAlex.
        Only replaces placeholder zeros or nulls.
        """
        try:
            # Extract necessary fields
            total_citations = openalex_data.get('cited_by_count', None)
            influential_citations = len(openalex_data.get('referenced_works', []))
            abstract_inverted_index = openalex_data.get('abstract_inverted_index', None)
            abstract = self.reconstruct_abstract(abstract_inverted_index)

            # Prepare fields to update
            update_fields = {}
            if total_citations is not None:
                update_fields['total_citations'] = total_citations
            if influential_citations is not None:
                update_fields['influential_citations'] = influential_citations
            if abstract:
                update_fields['abstract'] = abstract

            if not update_fields:
                print(f"No relevant data to update for paper ID {paper_id}.")
                return

            # Update the paper entry
            set_clause = ', '.join([
                f"{field} = CASE WHEN {field} IS NULL OR {field} = 0 THEN %s ELSE {field} END" 
                for field in update_fields.keys()
            ])
            values = list(update_fields.values())
            values.append(paper_id)

            update_query = f"""
                UPDATE papers
                SET {set_clause}
                WHERE id = %s
            """

            self.cursor.execute(update_query, values)
            print(f"Paper ID {paper_id} updated successfully with data from OpenAlex.")
        except psycopg2.Error as e:
            print(f"Error updating paper ID {paper_id}: {e}")

    def reconstruct_abstract(self, abstract_inverted_index):
        """
        Reconstruct the abstract from the inverted index provided by OpenAlex.
        """
        if not abstract_inverted_index:
            return None
        try:
            all_positions = [pos for positions in abstract_inverted_index.values() for pos in positions]
            if all_positions:
                max_position = max(all_positions)
                abstract_words = [None] * (max_position + 1)
                for word, positions in abstract_inverted_index.items():
                    for pos in positions:
                        abstract_words[pos] = word
                abstract = ' '.join(filter(None, abstract_words))
            else:
                abstract = ''
            return abstract
        except Exception as e:
            print(f"Error reconstructing abstract: {e}")
            return None

    def insert_admin(self, email: str):
        query = sql.SQL("INSERT INTO admins(email) VALUES ({email})").format(email=sql.Placeholder())
        try:
            self.cursor.execute(query, [email])
            return None
        except Exception as e:
            return e
        
    def remove_admin(self, email: str):
        query = sql.SQL("DELETE FROM admins WHERE email = {email}").format(email=sql.Placeholder())
        try:
            self.cursor.execute(query, [email])
            return None
        except Exception as e:
            return e
                
    def get_admins(self):
        query = sql.SQL("SELECT * FROM admins")
        try:
            self.cursor.execute(query, [])
            return self.cursor.fetchall()
        except Exception as e:
            return e

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
                total_journals=20,
                mean_journal_citations_per_paper=100.0
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
