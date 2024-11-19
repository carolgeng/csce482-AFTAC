
# for oauth
import json
import os
import time
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
from dotenv import load_dotenv

# to export csv
import csv
from io import StringIO

# for article serach app
import reflex as rx
from APIs.arXiv.arXiv_wrapper import api_handler
from datetime import datetime

# gets client id from env file
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')


# structure that holds the contents of the search results 
class Article(rx.Base):
    title: str
    authors: str
    summary: str
    pdf_url: str
    published: str
    comment: str = ""
    journal_ref: str = ""


class State(rx.State):

    # for oauth use token instead of goole client secret 
    id_token_json: str = rx.LocalStorage()

    def on_success(self, id_token: dict):
        """Handle successful login and store the ID token."""
        self.id_token_json = json.dumps(id_token)
        return rx.redirect("/user")

    @rx.var(cache=True)
    def tokeninfo(self) -> dict[str, str]:
        """Verify and parse the user's ID token."""
        try:
            return verify_oauth2_token(
                json.loads(self.id_token_json)[
                    "credential"
                ],
                requests.Request(),
                CLIENT_ID,
            )
        except Exception as exc:
            if self.id_token_json:
                print(f"Error verifying token: {exc}")
        return {}

    def logout(self):
        """Log the user out by clearing the ID token."""
        self.id_token_json = ""
        return rx.redirect("/")

    @rx.var
    def token_is_valid(self) -> bool:
        """Check if the user's token is valid."""
        try:
            return bool(
                self.tokeninfo
                and int(self.tokeninfo.get("exp", 0))
                > time.time()
            )
        except Exception:
            return False

    """State for managing user data and article search."""
    # store the user's input keywords
    keywords: str = ""
    # store the user's desired number of articles as a string
    num_articles: str = "10"  # Default value
    # store the search results as a list of Article models
    results: list[Article] = []

    def set_keywords(self, value):
        """Set the search keywords."""
        self.keywords = value

    def set_num_articles(self, value):
        """Set the number of articles."""
        self.num_articles = value

    def search_articles(self):
        """Function to handle article search."""
        handler = api_handler()
        # Convert num_articles to int
        try:
            num_articles_int = int(self.num_articles)
        except ValueError:
            num_articles_int = 10  # Default or handle error

        # Get the generator of results
        results_generator = handler.query(self.keywords, num_articles_int)
        
        # Initialize an empty list to store articles
        self.results = []
        for result in results_generator:
            # Convert published to string
            published_str = result.published.strftime('%Y-%m-%d %H:%M:%S') if result.published else ''

            # Ensure journal_ref is a string
            journal_ref = getattr(result, 'journal_ref', '') or ''

            # Create Article instance
            article = Article(
                title=result.title,
                authors=', '.join([author.name for author in result.authors]),
                summary=result.summary,
                pdf_url=result.pdf_url,
                published=published_str,
                comment=(getattr(result, 'comment', '') or ''),
                journal_ref=journal_ref,
            )
            self.results.append(article)

    def clear_results(self):
        """Clear the search results and reset input fields."""
        self.results = []
        self.keywords = ""
        self.num_articles = "10"

    @rx.event
    def export_results_to_csv(self):
        """Export search results to a CSV with title, authors, and published date."""
        if not self.results:
            print("No results to export!")
            return
        
        output = StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL) # for nicer formatting
        
        # header
        writer.writerow(["Title", "Authors", "Published"])
        
        # data
        for article in self.results:
            writer.writerow([
                article.title,
                article.authors,
                article.published,
            ])
        
        output.seek(0)
        filename = "search_results.csv"

        return rx.download(
            data=output.getvalue(),
            filename=filename,
        )