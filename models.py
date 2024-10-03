from database import db


class Paper(db.Model):
    __tablename__ = 'papers'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    abstract = db.Column(db.Text)
    publication_year = db.Column(db.Integer, nullable=False)
    journal_id = db.Column(db.Integer, db.ForeignKey('journals.id'))
    total_citations = db.Column(db.Integer)
    max_citations = db.Column(db.Integer)
    citations_per_year = db.Column(db.Integer)
    rank_citations_per_year = db.Column(db.Integer)

    journal = db.relationship('Journal', back_populates='papers')


class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    first_publication_year = db.Column(db.Integer)
    author_age = db.Column(db.Integer)
    h_index = db.Column(db.Integer)
    delta_h_index = db.Column(db.Integer)
    adopters = db.Column(db.Integer)
    total_papers = db.Column(db.Integer)
    delta_total_papers = db.Column(db.Integer)
    recent_coauthors = db.Column(db.Integer)

    papers = db.relationship('Paper', secondary='paper_authors', back_populates='authors')


class Journal(db.Model):
    __tablename__ = 'journals'
    id = db.Column(db.Integer, primary_key=True)
    journal_name = db.Column(db.String(255), nullable=False)
    mean_citations_per_paper = db.Column(db.Float)
    delta_mean_citations_per_paper = db.Column(db.Float)
    journal_h_index = db.Column(db.Integer)
    delta_journal_h_index = db.Column(db.Integer)
    max_citations_paper = db.Column(db.Integer)
    total_papers_published = db.Column(db.Integer)
    delta_total_papers_published = db.Column(db.Integer)

    papers = db.relationship('Paper', back_populates='journal')


class Citation(db.Model):
    __tablename__ = 'citations'
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))
    citation_year = db.Column(db.Integer)
    citation_count = db.Column(db.Integer)

    paper = db.relationship('Paper')
    author = db.relationship('Author')


class PaperAuthors(db.Model):
    __tablename__ = 'paper_authors'
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), primary_key=True)
