import reflex as rx

# structure that holds the contents of the search results 
class Article(rx.Base):
    title: str
    authors: str
    summary: str
    pdf_url: str
    published: int
    journal_ref: str = ""
    cit_count: int = 0 
    im_score: float = 0.0
