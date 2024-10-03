# models.py
from database import db

# Association table for the many-to-many relationship between papers and authors
paper_authors = db.Table('paper_authors',
    db.Column('paper_id', db.Integer, db.ForeignKey('paper.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)

class Paper(db.Model):
    __tablename__ = 'paper'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=True)
    abstract = db.Column(db.Text, nullable=True)
    publication_year = db.Column(db.Integer, nullable=True)
    raw_content = db.Column(db.Text, nullable=True)  # Store raw text for future processing
    journal_id = db.Column(db.Integer, db.ForeignKey('journals.id'), nullable=True)

    # Relationship to authors
    authors = db.relationship('Author', secondary=paper_authors, back_populates='papers')
    # Relationship to journal
    journal = db.relationship('Journal', back_populates='papers')

class Author(db.Model):
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)

    # Relationship to papers
    papers = db.relationship('Paper', secondary=paper_authors, back_populates='authors')

class Journal(db.Model):
    __tablename__ = 'journals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)

    # Relationship to papers
    papers = db.relationship('Paper', back_populates='journal')
