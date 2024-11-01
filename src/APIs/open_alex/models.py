# models.py

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, create_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from config import DATABASE_URL

Base = declarative_base()

class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    openalex_id = Column(String(50), unique=True)
    name = Column(String(500), nullable=False)
    first_publication_year = Column(Integer)
    author_age = Column(Integer)
    h_index = Column(Integer)
    delta_h_index = Column(Integer)
    adopters = Column(Integer)
    total_papers = Column(Integer)
    delta_total_papers = Column(Integer)
    recent_coauthors = Column(Integer)
    coauthor_pagerank = Column(Float)
    total_citations = Column(Integer)

    papers = relationship('PaperAuthor', back_populates='author', cascade='all, delete-orphan')
    citations = relationship('Citation', back_populates='author')

class Journal(Base):
    __tablename__ = 'journals'

    id = Column(Integer, primary_key=True)
    journal_name = Column(String(255), nullable=False)
    mean_citations_per_paper = Column(Float)
    delta_mean_citations_per_paper = Column(Float)
    journal_h_index = Column(Integer)
    delta_journal_h_index = Column(Integer)
    max_citations_paper = Column(Integer)
    total_papers_published = Column(Integer)
    delta_total_papers_published = Column(Integer)

    papers = relationship('Paper', back_populates='journal')

class Paper(Base):
    __tablename__ = 'papers'

    id = Column(Integer, primary_key=True)
    openalex_id = Column(String(50), unique=True)
    title = Column(String(2000), nullable=False)
    abstract = Column(Text)
    publication_year = Column(Integer)
    journal_id = Column(Integer, ForeignKey('journals.id'))
    total_citations = Column(Integer)
    citations_per_year = Column(Float)
    rank_citations_per_year = Column(Integer)
    pdf_url = Column(String(1000))
    doi = Column(String(255), unique=True)
    influential_citations = Column(Integer)
    delta_citations = Column(Integer)

    journal = relationship('Journal', back_populates='papers')
    authors = relationship('PaperAuthor', back_populates='paper')

    # Resolve ambiguity by specifying foreign_keys
    # Incoming citations (papers that cite this paper)
    citations = relationship('Citation', foreign_keys='Citation.paper_id', back_populates='paper')
    # Outgoing citations (papers cited by this paper)
    citing_citations = relationship('Citation', foreign_keys='Citation.citing_paper_id', back_populates='citing_paper')

class PaperAuthor(Base):
    __tablename__ = 'paper_authors'
    paper_id = Column(Integer, ForeignKey('papers.id'), primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.id'), primary_key=True)
    paper = relationship('Paper', back_populates='authors')
    author = relationship('Author', back_populates='papers')

class Citation(Base):
    __tablename__ = 'citations'

    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.id'))  # The paper being cited
    author_id = Column(Integer, ForeignKey('authors.id'))
    citation_year = Column(Integer)
    citation_count = Column(Integer)
    citing_paper_id = Column(Integer, ForeignKey('papers.id'))  # The paper that cites

    # Resolve ambiguity by specifying foreign_keys
    paper = relationship('Paper', foreign_keys=[paper_id], back_populates='citations')
    citing_paper = relationship('Paper', foreign_keys=[citing_paper_id], back_populates='citing_citations')
    author = relationship('Author', back_populates='citations')

# Optional: Define the Concept and PaperConcept models if you wish to store concepts
class Concept(Base):
    __tablename__ = 'concepts'

    id = Column(Integer, primary_key=True)
    openalex_id = Column(String(50), unique=True)
    name = Column(String(255))

    papers = relationship('PaperConcept', back_populates='concept', cascade='all, delete-orphan')

class PaperConcept(Base):
    __tablename__ = 'paper_concepts'

    paper_id = Column(Integer, ForeignKey('papers.id'), primary_key=True)
    concept_id = Column(Integer, ForeignKey('concepts.id'), primary_key=True)
    score = Column(Float)  # Relevance score

    paper = relationship('Paper', back_populates='concepts')
    concept = relationship('Concept', back_populates='papers')

Paper.concepts = relationship('PaperConcept', back_populates='paper', cascade='all, delete-orphan')

# No need to create tables since they already exist
