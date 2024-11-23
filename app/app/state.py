import os
import reflex as rx
from dotenv import load_dotenv

# for oauth
import json
import time
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token

# for article serach app
from .article import Article
from model.RankModel import RankModel
from database.populate_db import DatabaseSearchService

# to export csv
import csv
from io import StringIO

# gets client id from env file
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')


class State(rx.State):
    # for oauth use token instead of goole client secret 
    id_token_json: str = rx.LocalStorage()

    is_searching: bool = False
    is_populating: bool = False
    is_training: bool = False

    """State for managing user data and article search."""
    # store the user's input keywords
    keywords: str = ""
    # store the user's desired number of articles as a string
    num_articles: str = "" 
    # store the search results as a list of Article models
    results: list[Article] = []

    #UI components functions

    def validate_input(self):
        """Handle the click of the search button with input validation."""
        if not self.keywords.strip():
            return rx.toast("Keywords cannot be empty.")
        if not self.num_articles.strip():
            return rx.toast("Number of articles cannot be empty.")
        try:
            num_articles_int = int(self.num_articles)
            if num_articles_int <= 0:
                return rx.toast("Number of articles must be a positive integer.")
        except ValueError:
            return rx.toast("Number of articles must be an integer.")


    @rx.event(background=True)
    async def search_articles(self):
        """Function to handle article search and ranking."""

        if a := self.validate_input(): return a

        async with self:
            self.is_searching = True
        

        num_articles_int = int(self.num_articles)

        rank_model = RankModel()
        # Get ranked articles from the model
        ranked_articles = rank_model.rank_articles(self.keywords, num_articles=num_articles_int)

        # Build up a new list to store articles
        new_results = []

        if ranked_articles.empty:
            print("No articles found for the given query.")
            async with self:
                self.results = []
                self.is_searching = False
            return

        for _, result in ranked_articles.iterrows():
            # Filter out None values in authors
            authors_list = [a for a in result['authors'] if a] if result['authors'] else []
            authors_str = ', '.join(authors_list) if authors_list else 'Unknown'

            article = Article(
                title=result['title'],
                authors=authors_str,
                summary=result['abstract'] or 'No abstract available.',
                pdf_url=result['pdf_url'] or '#',
                published=str(result['publication_year']) or 'Unknown',
                journal_ref="",  # Update if journal references are available
            )
            new_results.append(article)
            # Update the results and is_searching flag inside async with self
            async with self:
                self.results = new_results
                self.is_searching = False


    @rx.var
    def is_busy(self) -> bool:
        """Returns True if the system is currently searching or training."""
        return self.is_populating or self.is_training

    @rx.var
    def populate_button_color(self):
        """Returns 'white' when populating is in progress."""
        return "white" if self.is_populating else None

    @rx.var
    def retrain_button_color(self):
        """Returns 'white' when training is in progress."""
        return "white" if self.is_training else None
    

    @rx.event(background=True)
    async def populate_database(self):

        if a := self.validate_input(): return a

        async with self:
            self.is_populating = True


        num_articles_int = int(self.num_articles)
        
        # Initialize the DatabaseSearchService with the query (keywords) and number of articles
        search_service = DatabaseSearchService(query=self.keywords, num_articles=num_articles_int)

        # Run the search and store the results in the databases
        search_service.search_and_store()

        print(f"Database populated with {num_articles_int} articles for query '{self.keywords}'.")

          

        async with self:
            # Optionally clear results or reset fields after population  
            self.clear_results()
            self.is_populating = False

    @rx.event(background=True)
    async def retrain_model(self):
        async with self:
            self.is_training = True

        RankModel().train_ml_model()

        async with self:
            self.is_training = False

    
    def set_keywords(self, value):
        """Set the search keywords."""
        self.keywords = value

    def set_num_articles(self, value):
        """Set the number of articles."""
        self.num_articles = value

    def go_admin_page(self):
        self.clear_results()
        return rx.redirect("/admin")
    
    def go_back(self):
        self.clear_results()
        return rx.redirect("/user")


    def clear_results(self):
        """Clear the search results and reset input fields."""
        self.results = []
        self.keywords = ""
        self.num_articles = ""


    #Google OAUTH functions
    @rx.var(cache=True)
    def email(self) -> str:
        """Extract the user's email from tokeninfo."""
        tokeninfo = self.tokeninfo  # Access the reactive tokeninfo variable
        # If tokeninfo exists and has an 'email' key, return it, otherwise return an empty string
        return tokeninfo["email"] if "email" in tokeninfo else ""

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
        
    def on_success(self, id_token: dict):
        """Handle successful login and store the ID token."""
        self.id_token_json = json.dumps(id_token)
        return rx.redirect("/user")
    
    def logout(self):
        """Log the user out by clearing the ID token."""
        self.id_token_json = ""
        self.clear_results()
        return rx.redirect("/")


    #export CSV functions
    @rx.event
    def export_results_to_csv(self):
        """Export search results to a CSV with title, authors, and published date."""
        if not self.results:
            print("No results to export!")
            return
        
        output = StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL) # for nicer formatting
        
        # header
        writer.writerow(["Title", "Authors", "Published", "PDF link"])
        
        # data
        for article in self.results:
            writer.writerow([
                article.title,
                article.authors,
                article.published,
                article.pdf_url
            ])
        
        output.seek(0)
        filename = "search_results.csv"

        return rx.download(
            data=output.getvalue(),
            filename=filename,
        )