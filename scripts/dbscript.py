import sqlite3

def create_database(filepath):
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(filepath)
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute('PRAGMA foreign_keys = ON;')

    # Create the 'journals' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS journals (
        id INTEGER PRIMARY KEY,
        journal_name TEXT NOT NULL,
        mean_citations_per_paper REAL,
        delta_mean_citations_per_paper REAL,
        journal_h_index INTEGER,
        delta_journal_h_index INTEGER,
        max_citations_paper INTEGER,
        total_papers_published INTEGER,
        delta_total_papers_published INTEGER
    );
    ''')

    # Create the 'authors' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        first_publication_year INTEGER,
        author_age INTEGER,
        h_index INTEGER,
        delta_h_index INTEGER,
        adopters INTEGER,
        total_papers INTEGER,
        delta_total_papers INTEGER,
        recent_coauthors INTEGER
    );
    ''')

    # Create the 'papers' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        abstract TEXT,
        publication_year INTEGER NOT NULL,
        journal_id INTEGER,
        total_citations INTEGER,
        max_citations INTEGER,
        citations_per_year INTEGER,
        rank_citations_per_year INTEGER,
        pdf_url TEXT,
        doi TEXT,
        FOREIGN KEY (journal_id) REFERENCES journals(id)
    );
    ''')

    # Create the 'paper_authors' association table for many-to-many relationship
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS paper_authors (
        paper_id INTEGER,
        author_id INTEGER,
        PRIMARY KEY (paper_id, author_id),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
    );
    ''')

    # Create the 'paper_figures' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS paper_figures (
        id INTEGER PRIMARY KEY,
        paper_id INTEGER,
        figure_url TEXT,
        caption TEXT,
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
    );
    ''')

    # Create the 'paper_external_ids' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS paper_external_ids (
        id INTEGER PRIMARY KEY,
        paper_id INTEGER,
        arxiv_id TEXT,
        doi TEXT,
        pubmed_id TEXT,
        dblp_id TEXT,
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
    );
    ''')

    # Create the 'citations' table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS citations (
        id INTEGER PRIMARY KEY,
        paper_id INTEGER,
        author_id INTEGER,
        citation_year INTEGER,
        citation_count INTEGER,
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
    );
    ''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Database and tables created successfully.")
