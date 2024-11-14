#!/bin/bash

# Change to the root directory
cd "$(dirname "$0")"/..

# Remove the existing SQLite database file
rm -f data.db

# Create a new SQLite database and execute the schema
sqlite3 data.db <<EOF
-- Drop existing tables to ensure a clean reset
DROP TABLE IF EXISTS paper_concepts;
DROP TABLE IF EXISTS concepts;
DROP TABLE IF EXISTS citations;
DROP TABLE IF EXISTS paper_authors;
DROP TABLE IF EXISTS papers;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS journals;

-- Create the 'authors' table
CREATE TABLE authors (
    id INTEGER PRIMARY KEY,
    openalex_id VARCHAR(50) UNIQUE,
    name VARCHAR(500) NOT NULL,
    first_publication_year INTEGER,
    author_age INTEGER,
    h_index INTEGER,
    delta_h_index INTEGER,
    adopters INTEGER,
    total_papers INTEGER,
    delta_total_papers INTEGER,
    recent_coauthors INTEGER,
    coauthor_pagerank FLOAT,
    total_citations INTEGER,
    citations_per_paper FLOAT,
    max_citations INTEGER,
    total_journals INTEGER,
    mean_journal_citations_per_paper FLOAT
);

-- Create the 'journals' table
CREATE TABLE journals (
    id INTEGER PRIMARY KEY,
    journal_name VARCHAR(255) NOT NULL,
    mean_citations_per_paper FLOAT,
    delta_mean_citations_per_paper FLOAT,
    journal_h_index INTEGER,
    delta_journal_h_index INTEGER,
    max_citations_paper INTEGER,
    total_papers_published INTEGER,
    delta_total_papers_published INTEGER
);

-- Create the 'papers' table
CREATE TABLE papers (
    id INTEGER PRIMARY KEY,
    openalex_id VARCHAR(50) UNIQUE,
    title VARCHAR(2000) NOT NULL,
    abstract TEXT,
    publication_year INTEGER,
    journal_id INTEGER,
    total_citations INTEGER,
    citations_per_year FLOAT,
    rank_citations_per_year INTEGER,
    pdf_url VARCHAR(1000),
    doi VARCHAR(255) UNIQUE,
    influential_citations INTEGER,
    delta_citations INTEGER,
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

-- Create the 'citations' table
CREATE TABLE citations (
    id INTEGER PRIMARY KEY,
    paper_id INTEGER,
    author_id INTEGER,
    citation_year INTEGER,
    citation_count INTEGER,
    citing_paper_id INTEGER,
    FOREIGN KEY(paper_id) REFERENCES papers(id),
    FOREIGN KEY(author_id) REFERENCES authors(id),
    FOREIGN KEY(citing_paper_id) REFERENCES papers(id)
);

-- Create the 'concepts' table
CREATE TABLE concepts (
    id INTEGER PRIMARY KEY,
    openalex_id VARCHAR(50) UNIQUE,
    name VARCHAR(255)
);

-- Create the 'paper_concepts' association table
CREATE TABLE paper_concepts (
    paper_id INTEGER NOT NULL,
    concept_id INTEGER NOT NULL,
    score FLOAT,
    PRIMARY KEY (paper_id, concept_id),
    FOREIGN KEY(paper_id) REFERENCES papers(id),
    FOREIGN KEY(concept_id) REFERENCES concepts(id)
);
EOF

echo "Database has been reset and schema has been applied."
