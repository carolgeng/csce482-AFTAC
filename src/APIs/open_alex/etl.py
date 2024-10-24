# etl.py
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Paper, Author, Journal, Citation, PaperAuthor
from config import DATABASE_URL
import datetime
import time

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def fetch_papers(query, per_page=200, max_pages=5):
    base_url = 'https://api.openalex.org/works'
    headers = {'User-Agent': 'AI_Driven_RD (alecklem@tamu.edu)'}
    params = {
        'search': query,
        'per-page': per_page,
        'cursor': '*'
    }
    papers = []
    page = 1
    while page <= max_pages:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching page {page}: {response.status_code}")
            break
        data = response.json()
        papers.extend(data['results'])
        cursor = data['meta'].get('next_cursor')
        if not cursor or cursor == 'false':
            break
        params['cursor'] = cursor
        page += 1
        time.sleep(1)  # Respect API rate limits
    return papers

def process_papers(papers):
    for paper_data in papers:
        paper_id = paper_data['id']
        title = paper_data.get('title')
        abstract_inverted_index = paper_data.get('abstract_inverted_index')
        if abstract_inverted_index:
            # Reconstruct abstract from inverted index
            abstract = ' '.join(sorted(abstract_inverted_index, key=abstract_inverted_index.get))
        else:
            abstract = None
        publication_date = paper_data.get('publication_date')
        if publication_date:
            try:
                publication_date = datetime.datetime.strptime(publication_date, '%Y-%m-%d').date()
            except ValueError:
                publication_date = None
        total_citations = paper_data.get('cited_by_count', 0)
        authorships = paper_data.get('authorships', [])
        journal_data = paper_data.get('host_venue', {})

        # Create or get Journal
        journal_id = journal_data.get('id')
        journal = None
        if journal_id:
            journal = session.query(Journal).get(journal_id)
            if not journal:
                journal_name = journal_data.get('display_name')
                journal = Journal(
                    journal_id=journal_id,
                    journal_name=journal_name
                )
                session.add(journal)
                session.commit()

        # Check if paper already exists
        existing_paper = session.query(Paper).get(paper_id)
        if existing_paper:
            continue  # Skip if paper already exists

        # Create Paper
        paper = Paper(
            paper_id=paper_id,
            title=title,
            abstract=abstract,
            publication_date=publication_date,
            total_citations=total_citations,
            journal=journal
        )
        session.add(paper)
        session.commit()

        # Process Authors
        for author_data in authorships:
            author_info = author_data.get('author', {})
            author_id = author_info.get('id')
            if author_id:
                author = session.query(Author).get(author_id)
                if not author:
                    author_name = author_info.get('display_name')
                    author = Author(
                        author_id=author_id,
                        name=author_name
                    )
                    session.add(author)
                    session.commit()
                # Create PaperAuthor association
                paper_author = session.query(PaperAuthor).filter_by(paper_id=paper_id, author_id=author_id).first()
                if not paper_author:
                    affiliation_data = author_data.get('institutions', [])
                    affiliation = affiliation_data[0]['display_name'] if affiliation_data else None
                    paper_author = PaperAuthor(
                        paper_id=paper_id,
                        author_id=author_id,
                        affiliation=affiliation
                    )
                    session.add(paper_author)
        session.commit()

def calculate_author_indicators(author):
    # Fetch author's works to calculate h-index and other metrics
    base_url = 'https://api.openalex.org/works'
    headers = {'User-Agent': 'AI_Driven_RD (alecklem@tamu.edu)'}
    params = {
        'filter': f'author.id:{author.author_id}',
        'per-page': 200,
        'cursor': '*'
    }
    works = []
    while True:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching works for author {author.author_id}: {response.status_code}")
            break
        data = response.json()
        works.extend(data['results'])
        cursor = data['meta'].get('next_cursor')
        if not cursor or cursor == 'false':
            break
        params['cursor'] = cursor
        time.sleep(1)  # Respect API rate limits

    if not works:
        return

    # Calculate h-index
    citation_counts = [work.get('cited_by_count', 0) for work in works]
    citation_counts.sort(reverse=True)
    h_index = 0
    for i, citations in enumerate(citation_counts):
        if citations >= i + 1:
            h_index = i + 1
        else:
            break
    author.h_index = h_index

    # Calculate author age
    publication_years = [int(work['publication_year']) for work in works if work.get('publication_year')]
    if publication_years:
        first_publication_year = min(publication_years)
        author.first_publication_year = first_publication_year
        author.author_age = datetime.datetime.now().year - first_publication_year

    # Calculate total papers
    author.total_papers = len(works)

    session.commit()

def calculate_journal_indicators(journal):
    # Fetch journal's works to calculate indicators
    base_url = 'https://api.openalex.org/works'
    headers = {'User-Agent': 'AI_Driven_RD (alecklem@tamu.edu)'}
    params = {
        'filter': f'host_venue.id:{journal.journal_id}',
        'per-page': 200,
        'cursor': '*'
    }
    works = []
    while True:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching works for journal {journal.journal_id}: {response.status_code}")
            break
        data = response.json()
        works.extend(data['results'])
        cursor = data['meta'].get('next_cursor')
        if not cursor or cursor == 'false':
            break
        params['cursor'] = cursor
        time.sleep(1)  # Respect API rate limits

    if not works:
        return

    # Calculate mean citations per paper
    citation_counts = [work.get('cited_by_count', 0) for work in works]
    if citation_counts:
        journal.mean_citations_per_paper = sum(citation_counts) / len(citation_counts)
        journal.max_citations_paper = max(citation_counts)
    else:
        journal.mean_citations_per_paper = 0
        journal.max_citations_paper = 0

    # Calculate h-index
    citation_counts.sort(reverse=True)
    h_index = 0
    for i, citations in enumerate(citation_counts):
        if citations >= i + 1:
            h_index = i + 1
        else:
            break
    journal.journal_h_index = h_index

    # Total papers published
    journal.total_papers_published = len(works)

    session.commit()

def main():
    query = 'machine learning'  # Modify this query to target specific research areas
    papers = fetch_papers(query)
    process_papers(papers)

    # Calculate indicators for authors
    authors = session.query(Author).all()
    for author in authors:
        calculate_author_indicators(author)

    # Calculate indicators for journals
    journals = session.query(Journal).all()
    for journal in journals:
        calculate_journal_indicators(journal)

if __name__ == '__main__':
    main()
