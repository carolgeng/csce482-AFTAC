# etl.py
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper, Author, Journal, Citation, PaperAuthor
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
        # Check if paper already exists based on DOI
        doi = paper_data.get('doi')
        existing_paper = None
        if doi:
            existing_paper = session.query(Paper).filter_by(doi=doi).first()
        else:
            # If no DOI, use title to check for duplicates
            title = paper_data.get('title')
            existing_paper = session.query(Paper).filter_by(title=title).first()

        if existing_paper:
            continue  # Skip if paper already exists

        # Proceed to add new paper
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
                publication_year = datetime.datetime.strptime(publication_date, '%Y-%m-%d').year
            except ValueError:
                publication_year = None
        else:
            publication_year = None
        total_citations = paper_data.get('cited_by_count', 0)
        authorships = paper_data.get('authorships', [])
        journal_data = paper_data.get('host_venue', {})
        pdf_url = paper_data.get('primary_location', {}).get('pdf_url')
        influential_citations = paper_data.get('referenced_works_count', 0)

        # Create or get Journal
        journal_id = None
        journal_name = journal_data.get('display_name')
        if journal_name:
            journal = session.query(Journal).filter_by(journal_name=journal_name).first()
            if not journal:
                journal = Journal(
                    journal_name=journal_name
                )
                session.add(journal)
                session.commit()
            journal_id = journal.id
        else:
            journal = None

        # Create new Paper
        paper = Paper(
            title=title,
            abstract=abstract,
            publication_year=publication_year,
            journal_id=journal_id,
            total_citations=total_citations,
            pdf_url=pdf_url,
            doi=doi,
            influential_citations=influential_citations
        )
        session.add(paper)
        session.commit()

        # Process Authors
        for author_data in authorships:
            author_info = author_data.get('author', {})
            author_name = author_info.get('display_name')
            if not author_name:
                continue
            # Check if author already exists
            author = session.query(Author).filter_by(name=author_name).first()
            if not author:
                author = Author(
                    name=author_name
                )
                session.add(author)
                session.commit()
            # Create PaperAuthor association
            paper_author = session.query(PaperAuthor).filter_by(paper_id=paper.id, author_id=author.id).first()
            if not paper_author:
                paper_author = PaperAuthor(
                    paper_id=paper.id,
                    author_id=author.id
                )
                session.add(paper_author)
        session.commit()

def calculate_author_indicators(author):
    # Fetch author's works to calculate h-index and other metrics
    base_url = 'https://api.openalex.org/works'
    headers = {'User-Agent': 'AI_Driven_RD (alecklem@tamu.edu)'}
    params = {
        'filter': f'authorships.author.display_name:"{author.name}"',
        'per-page': 200,
        'cursor': '*'
    }
    works = []
    while True:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching works for author {author.name}: {response.status_code}")
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
    publication_years = [int(work.get('publication_year')) for work in works if work.get('publication_year')]
    if publication_years:
        first_publication_year = min(publication_years)
        author.first_publication_year = first_publication_year
        author.author_age = datetime.datetime.now().year - first_publication_year

    # Calculate total papers
    author.total_papers = len(works)

    # Update total citations
    author.total_citations = sum(citation_counts)

    session.commit()

def calculate_journal_indicators(journal):
    # Fetch journal's works to calculate indicators
    base_url = 'https://api.openalex.org/works'
    headers = {'User-Agent': 'AI_Driven_RD (alecklem@tamu.edu)'}
    params = {
        'filter': f'host_venue.display_name:"{journal.journal_name}"',
        'per-page': 200,
        'cursor': '*'
    }
    works = []
    while True:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching works for journal {journal.journal_name}: {response.status_code}")
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

def update_existing_papers():
    existing_papers = session.query(Paper).all()
    for paper in existing_papers:
        # Check for missing fields
        needs_update = False
        if not paper.abstract or not paper.publication_year or paper.total_citations is None:
            needs_update = True

        if needs_update:
            doi = paper.doi
            if doi:
                # Fetch data from OpenAlex using DOI
                base_url = f'https://api.openalex.org/works/doi:{doi}'
                headers = {'User-Agent': 'AI_Driven_RD (alecklem@tamu.edu)'}
                response = requests.get(base_url, headers=headers)
                if response.status_code != 200:
                    print(f"Error fetching data for DOI {doi}: {response.status_code}")
                    continue
                paper_data = response.json()
                # Update fields
                abstract_inverted_index = paper_data.get('abstract_inverted_index')
                if abstract_inverted_index:
                    abstract = ' '.join(sorted(abstract_inverted_index, key=abstract_inverted_index.get))
                    paper.abstract = abstract
                publication_date = paper_data.get('publication_date')
                if publication_date:
                    try:
                        publication_year = datetime.datetime.strptime(publication_date, '%Y-%m-%d').year
                        paper.publication_year = publication_year
                    except ValueError:
                        pass
                total_citations = paper_data.get('cited_by_count', 0)
                paper.total_citations = total_citations
                influential_citations = paper_data.get('referenced_works_count', 0)
                paper.influential_citations = influential_citations
                # Update journal
                journal_data = paper_data.get('host_venue', {})
                journal_name = journal_data.get('display_name')
                if journal_name:
                    journal = session.query(Journal).filter_by(journal_name=journal_name).first()
                    if not journal:
                        journal = Journal(
                            journal_name=journal_name
                        )
                        session.add(journal)
                        session.commit()
                    paper.journal_id = journal.id
                # Update authors
                authorships = paper_data.get('authorships', [])
                for author_data in authorships:
                    author_info = author_data.get('author', {})
                    author_name = author_info.get('display_name')
                    if not author_name:
                        continue
                    # Check if author already exists
                    author = session.query(Author).filter_by(name=author_name).first()
                    if not author:
                        author = Author(
                            name=author_name
                        )
                        session.add(author)
                        session.commit()
                    # Create PaperAuthor association if not exists
                    paper_author = session.query(PaperAuthor).filter_by(paper_id=paper.id, author_id=author.id).first()
                    if not paper_author:
                        paper_author = PaperAuthor(
                            paper_id=paper.id,
                            author_id=author.id
                        )
                        session.add(paper_author)
                session.commit()
            else:
                print(f"No DOI for paper ID {paper.id}, cannot update")
    print("Finished updating existing papers")

def main():
    # Update existing papers with missing information
    update_existing_papers()

    # Fetch and process new papers
    query = 'machine learning'  # Modify this query as needed
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
