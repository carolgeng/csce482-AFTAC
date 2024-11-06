#!/bin/bash

# Remove the existing SQLite database file
rm -f data.db

# Create a new SQLite database and execute the schema
sqlite3 data.db <<EOF
-- Drop tables if they exist to ensure a clean reset
DROP TABLE IF EXISTS citations;
DROP TABLE IF EXISTS paper_authors;
DROP TABLE IF EXISTS paper_figures;
DROP TABLE IF EXISTS paper_external_ids;
DROP TABLE IF EXISTS papers;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS journals;

-- Create the 'authors' table
CREATE TABLE authors (
    id INTEGER PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    first_publication_year INTEGER,
    author_age INTEGER,
    h_index INTEGER DEFAULT 0,
    delta_h_index INTEGER,
    adopters INTEGER DEFAULT 0,
    total_papers INTEGER DEFAULT 0,
    delta_total_papers INTEGER,
    recent_coauthors INTEGER,
    coauthor_pagerank FLOAT DEFAULT 0.0,
    total_citations INTEGER DEFAULT 0
);

-- Create the 'journals' table
CREATE TABLE journals (
    id INTEGER PRIMARY KEY,
    journal_name VARCHAR(255) NOT NULL,
    mean_citations_per_paper FLOAT DEFAULT 0.0,
    delta_mean_citations_per_paper FLOAT,
    journal_h_index INTEGER DEFAULT 0,
    delta_journal_h_index INTEGER,
    max_citations_paper INTEGER,
    total_papers_published INTEGER DEFAULT 0,
    delta_total_papers_published INTEGER
);

-- Create the 'papers' table
CREATE TABLE papers (
    id INTEGER PRIMARY KEY,
    corpus_id INTEGER UNIQUE,
    title VARCHAR(2000) NOT NULL,
    abstract TEXT,
    publication_year INTEGER,
    journal_id INTEGER,
    total_citations INTEGER DEFAULT 0,
    influential_citations INTEGER DEFAULT 0,
    delta_citations INTEGER DEFAULT 0,
    citations_per_year FLOAT DEFAULT 0.0,
    rank_citations_per_year INTEGER,
    pdf_url VARCHAR(1000),
    doi VARCHAR(255),
    FOREIGN KEY(journal_id) REFERENCES journals(id)
);

-- Create the 'paper_authors' association table
CREATE TABLE paper_authors (
    paper_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    PRIMARY KEY (paper_id, author_id),
    FOREIGN KEY(paper_id) REFERENCES papers(id),
    FOREIGN KEY(author_id) REFERENCES authors(id)
);

-- Create the 'paper_external_ids' table
CREATE TABLE paper_external_ids (
    id INTEGER PRIMARY KEY,
    paper_id INTEGER NOT NULL,
    arxiv_id VARCHAR(255),
    doi VARCHAR(255),
    pubmed_id VARCHAR(255),
    dblp_id VARCHAR(255),
    FOREIGN KEY(paper_id) REFERENCES papers(id)
);

-- Create the 'paper_figures' table
CREATE TABLE paper_figures (
    id INTEGER PRIMARY KEY,
    paper_id INTEGER NOT NULL,
    figure_id VARCHAR(255),
    caption TEXT,
    FOREIGN KEY(paper_id) REFERENCES papers(id)
);

-- Create the 'citations' table
CREATE TABLE citations (
    id INTEGER PRIMARY KEY,
    paper_id INTEGER,
    author_id INTEGER,
    citation_year INTEGER,
    citation_count INTEGER DEFAULT 0,
    citing_paper_id INTEGER,
    FOREIGN KEY(paper_id) REFERENCES papers(id),
    FOREIGN KEY(author_id) REFERENCES authors(id),
    FOREIGN KEY(citing_paper_id) REFERENCES papers(id)
);
EOF

echo "Database has been reset and schema has been applied."
