# app/database/compute_metrics.py

import sys
import datetime
import logging
import traceback
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from ..models import Base, Paper, Author, Journal, Citation, PaperAuthor, Concept, PaperConcept
from dotenv import load_dotenv
import os
import networkx as nx

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("compute_metrics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def connect_to_database():
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))
        Session = scoped_session(sessionmaker(bind=engine))
        session = Session()
        logger.info("Database connection successful.")
        return session
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)

def compute_author_metrics(session):
    current_year = datetime.datetime.now().year
    authors = session.query(Author).all()
    total_authors = len(authors)
    logger.info(f"Computing metrics for {total_authors} authors.")

    for idx, author in enumerate(authors, start=1):
        try:
            if idx % 100 == 0:
                logger.info(f"Processing author {idx}/{total_authors}")

            # Get all papers authored
            papers = session.query(Paper).join(PaperAuthor).filter(PaperAuthor.author_id == author.id).all()
            total_papers = len(papers)
            author.total_papers = total_papers

            # Calculate delta_total_papers (change in total_papers)
            # For simplicity, we'll assume delta is zero since we don't have historical data
            author.delta_total_papers = 0  # Update this as needed

            if total_papers == 0:
                continue  # Skip authors with no papers

            # Total citations
            total_citations = sum(paper.total_citations or 0 for paper in papers)
            author.total_citations = total_citations

            # Citations per paper
            citations_per_paper = total_citations / total_papers
            author.citations_per_paper = citations_per_paper

            # Maximum citations
            max_citations = max(paper.total_citations or 0 for paper in papers)
            author.max_citations = max_citations

            # h-index calculation
            citation_counts = sorted([paper.total_citations or 0 for paper in papers], reverse=True)
            h_index = 0
            for i, c in enumerate(citation_counts, start=1):
                if c >= i:
                    h_index = i
                else:
                    break

            # Calculate delta_h_index (change in h_index)
            previous_h_index = author.h_index or 0
            author.delta_h_index = h_index - previous_h_index
            author.h_index = h_index

            # Author age
            publication_years = [paper.publication_year for paper in papers if paper.publication_year]
            if publication_years:
                first_publication_year = min(publication_years)
                author.first_publication_year = first_publication_year
                author.author_age = current_year - first_publication_year
            else:
                author.first_publication_year = None
                author.author_age = None

            # Recent coauthors (last 5 years)
            recent_year_threshold = current_year - 5
            recent_papers = [paper for paper in papers if paper.publication_year and paper.publication_year >= recent_year_threshold]
            recent_coauthor_ids = set()
            for paper in recent_papers:
                coauthor_ids = [pa.author_id for pa in paper.authors if pa.author_id != author.id]
                recent_coauthor_ids.update(coauthor_ids)
            author.recent_coauthors = len(recent_coauthor_ids)

            # Total journals published in
            journal_ids = set(paper.journal_id for paper in papers if paper.journal_id)
            author.total_journals = len(journal_ids)

            # Mean journal citations per paper
            journal_citations = []
            for paper in papers:
                if paper.journal and paper.total_citations is not None:
                    journal_citations.append(paper.total_citations)
            if journal_citations:
                author.mean_journal_citations_per_paper = sum(journal_citations) / len(journal_citations)
            else:
                author.mean_journal_citations_per_paper = None

            # Save changes
            session.add(author)

        except Exception as e:
            logger.error(f"Error computing metrics for author {author.id}: {e}")
            logger.error(traceback.format_exc())
            continue

    # Commit all changes
    try:
        session.commit()
        logger.info("Author metrics computed and committed successfully.")
    except Exception as e:
        logger.error(f"Error committing author metrics: {e}")
        logger.error(traceback.format_exc())
        session.rollback()

def compute_paper_metrics(session):
    current_year = datetime.datetime.now().year
    papers = session.query(Paper).all()
    total_papers = len(papers)
    logger.info(f"Computing metrics for {total_papers} papers.")

    # Prepare data for ranking
    papers_with_citations_per_year = []
    for idx, paper in enumerate(papers, start=1):
        try:
            if idx % 1000 == 0:
                logger.info(f"Processing paper {idx}/{total_papers}")

            if paper.publication_year:
                years_since_publication = current_year - paper.publication_year + 1
                if years_since_publication > 0:
                    citations_per_year = (paper.total_citations or 0) / years_since_publication
                else:
                    citations_per_year = paper.total_citations or 0
                paper.citations_per_year = citations_per_year
                papers_with_citations_per_year.append((paper.id, citations_per_year))
            else:
                paper.citations_per_year = None

            # Save changes
            session.add(paper)

        except Exception as e:
            logger.error(f"Error computing metrics for paper {paper.id}: {e}")
            logger.error(traceback.format_exc())
            continue

    # Rank papers based on citations per year
    papers_with_citations_per_year.sort(key=lambda x: x[1], reverse=True)
    for rank, (paper_id, _) in enumerate(papers_with_citations_per_year, start=1):
        try:
            paper = session.query(Paper).get(paper_id)
            if paper:
                paper.rank_citations_per_year = rank
                session.add(paper)
        except Exception as e:
            logger.error(f"Error ranking paper ID {paper_id}: {e}")
            logger.error(traceback.format_exc())
            continue

    # Commit all changes
    try:
        session.commit()
        logger.info("Paper metrics computed and committed successfully.")
    except Exception as e:
        logger.error(f"Error committing paper metrics: {e}")
        logger.error(traceback.format_exc())
        session.rollback()

def compute_journal_metrics(session):
    journals = session.query(Journal).all()
    total_journals = len(journals)
    logger.info(f"Computing metrics for {total_journals} journals.")

    for idx, journal in enumerate(journals, start=1):
        try:
            if idx % 100 == 0:
                logger.info(f"Processing journal {idx}/{total_journals}")

            papers = session.query(Paper).filter(Paper.journal_id == journal.id).all()
            total_papers = len(papers)
            previous_total_papers = journal.total_papers_published or 0
            journal.total_papers_published = total_papers
            journal.delta_total_papers_published = total_papers - previous_total_papers

            if total_papers == 0:
                continue  # Skip journals with no papers

            # Mean citations per paper
            total_citations = sum(paper.total_citations or 0 for paper in papers)
            journal.mean_citations_per_paper = total_citations / total_papers

            # Delta mean citations per paper (change since last computation)
            previous_mean_citations = journal.mean_citations_per_paper or 0
            journal.delta_mean_citations_per_paper = journal.mean_citations_per_paper - previous_mean_citations

            # Maximum citations per paper
            max_citations = max(paper.total_citations or 0 for paper in papers)
            journal.max_citations_paper = max_citations

            # Journal h-index
            citation_counts = sorted([paper.total_citations or 0 for paper in papers], reverse=True)
            h_index = 0
            for i, c in enumerate(citation_counts, start=1):
                if c >= i:
                    h_index = i
                else:
                    break

            # Delta journal h-index
            previous_h_index = journal.journal_h_index or 0
            journal.delta_journal_h_index = h_index - previous_h_index
            journal.journal_h_index = h_index

            # Save changes
            session.add(journal)

        except Exception as e:
            logger.error(f"Error computing metrics for journal {journal.id}: {e}")
            logger.error(traceback.format_exc())
            continue

    # Commit all changes
    try:
        session.commit()
        logger.info("Journal metrics computed and committed successfully.")
    except Exception as e:
        logger.error(f"Error committing journal metrics: {e}")
        logger.error(traceback.format_exc())
        session.rollback()

def compute_coauthor_pagerank(session):
    logger.info("Computing coauthor PageRank.")
    try:
        # Build the coauthorship network
        G = nx.Graph()
        paper_authors = session.query(PaperAuthor).all()
        for pa in paper_authors:
            G.add_node(pa.author_id)
        papers = session.query(Paper).all()
        for paper in papers:
            author_ids = [pa.author_id for pa in paper.authors]
            for i in range(len(author_ids)):
                for j in range(i + 1, len(author_ids)):
                    G.add_edge(author_ids[i], author_ids[j])

        # Compute PageRank
        pagerank = nx.pagerank(G)
        # Update authors with PageRank scores
        for author_id, score in pagerank.items():
            try:
                author = session.query(Author).get(author_id)
                if author:
                    author.coauthor_pagerank = score
                    session.add(author)
            except Exception as e:
                logger.error(f"Error updating coauthor_pagerank for author {author_id}: {e}")
                logger.error(traceback.format_exc())
                continue

        # Commit changes
        session.commit()
        logger.info("Coauthor PageRank computed and committed successfully.")
    except Exception as e:
        logger.error(f"Error computing coauthor PageRank: {e}")
        logger.error(traceback.format_exc())
        session.rollback()

def main():
    session = connect_to_database()

    compute_author_metrics(session)
    compute_paper_metrics(session)
    compute_journal_metrics(session)
    compute_coauthor_pagerank(session)

    # Close the session
    session.close()

if __name__ == '__main__':
    main()
