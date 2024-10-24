# models.py
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from config import DATABASE_URL

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'

    paper_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    abstract = Column(String)
    publication_date = Column(Date)
    journal_id = Column(String, ForeignKey('journals.journal_id'))
    total_citations = Column(Integer)
    max_citations = Column(Integer)
    citations_per_year = Column(Float)
    rank_citations_per_year = Column(Integer)

    journal = relationship('Journal', back_populates='papers')
    authors = relationship('PaperAuthor', back_populates='paper', cascade='all, delete-orphan')
    citations = relationship('Citation', back_populates='paper')

class Author(Base):
    __tablename__ = 'authors'

    author_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    first_publication_year = Column(Integer)
    author_age = Column(Integer)
    h_index = Column(Integer)
    delta_h_index = Column(Integer)
    adopters = Column(Integer)  # Unique citing authors
    total_papers = Column(Integer)
    delta_total_papers = Column(Integer)
    recent_coauthors = Column(Integer)

    papers = relationship('PaperAuthor', back_populates='author', cascade='all, delete-orphan')
    citations = relationship('Citation', back_populates='author')

class Journal(Base):
    __tablename__ = 'journals'

    journal_id = Column(String, primary_key=True)
    journal_name = Column(String, nullable=False)
    mean_citations_per_paper = Column(Float)
    delta_mean_citations_per_paper = Column(Float)
    journal_h_index = Column(Integer)
    delta_journal_h_index = Column(Integer)
    max_citations_paper = Column(Integer)
    total_papers_published = Column(Integer)
    delta_total_papers_published = Column(Integer)

    papers = relationship('Paper', back_populates='journal')

class Citation(Base):
    __tablename__ = 'citations'

    citation_id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String, ForeignKey('papers.paper_id'))
    author_id = Column(String, ForeignKey('authors.author_id'))
    citation_year = Column(Integer)
    citation_count = Column(Integer)

    paper = relationship('Paper', back_populates='citations')
    author = relationship('Author', back_populates='citations')

class PaperAuthor(Base):
    __tablename__ = 'paper_authors'

    paper_id = Column(String, ForeignKey('papers.paper_id'), primary_key=True)
    author_id = Column(String, ForeignKey('authors.author_id'), primary_key=True)
    affiliation = Column(String)

    paper = relationship('Paper', back_populates='authors')
    author = relationship('Author', back_populates='papers')

def create_tables():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_tables()
