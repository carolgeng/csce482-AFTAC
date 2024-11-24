import os
import reflex as rx
from dotenv import load_dotenv
from random import randint, random

# for oauth
import json
import time
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token

# for article serach app
from .article import Article
from model.RankModel import RankModel
from database.populate_db import DatabaseSearchService
from database.DatabaseManager import DatabaseManager

# to export csv
import csv
from io import StringIO

# gets client id from env file
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')

G_db_manager: DatabaseManager = DatabaseManager()

class State(rx.State):
    id_token_json: str = rx.LocalStorage()

    is_searching: bool = False
    is_populating: bool = False

    #default, ascending, descending
    sort_date_mode: str = "default"
    sort_citation_mode: str = "default"
    sort_score_mode: str = "default"

    date_label: str = "Sort by Date"
    citation_label: str = "Sort by Citations"
    score_label: str = "Sort by Impact Score"

    admin_entry: str = ""

    """State for managing user data and article search."""
    # store the user's input keywords
    keywords: str = ""
    # store the user's desired number of articles as a string
    num_articles: str = "" 
    # store the search results as a list of Article models
    original_results: list[Article] = []
    results: list[Article] = []

    def validate_input(self):
        """Handle the click of the search button with input validation."""
        if not self.keywords.strip():
            return rx.toast.warning("Keywords cannot be empty.")
        if not self.num_articles.strip():
            return rx.toast.warning("Number of articles cannot be empty.")
        try:
            num_articles_int = int(self.num_articles)
            if num_articles_int <= 0:
                return rx.toast.warning("Number of articles must be a positive integer.")
        except ValueError:
            return rx.toast.warning("Number of articles must be an integer.")

    @rx.event()
    def set_keywords(self, value: str):
        """Set the search keywords."""
        self.keywords = value

    @rx.event()
    def set_num_articles(self, value: str):
        """Set the number of articles."""
        self.num_articles = value

    def go_admin_page(self):
        self.clear_results()
        return rx.redirect("/admin")

    def go_search(self):
        self.clear_results()
        return rx.redirect("/search")
    
    def go_users(self):
        self.clear_results()
        return rx.redirect("/users")

    def clear_results(self):
        """Clear the search results and reset input fields."""
        self.results = []
        self.original_results = []
        self.keywords = ""
        self.num_articles = ""
        self.sort_date_mode = "default"
        self.admin_entry = ""

    @rx.var
    def get_admins(self) -> list[str]:
        try:
            return [t[1] for t in G_db_manager.get_admins()]
        except Exception:
            return rx.toast.error("Failed to display admins")
    
    @rx.event()
    def set_admin_entry(self, value: str):
        """Set the number of articles."""
        self.admin_entry = value

    @rx.event
    def add_admin(self):
        G_db_manager.insert_admin(self.admin_entry)
        self.clear_results()

    @rx.event
    def remove_admin(self, email: str):
        G_db_manager.remove_admin(email)

    #UI components functions
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
            async with self:
                self.results = []
                self.is_searching = False
            return rx.toast.error("No articles found for the given query.")

        for _, result in ranked_articles.iterrows():
            # Filter out None values in authors
            authors_list = [a for a in result['authors'] if a] if result['authors'] else []
            authors_str = ', '.join(authors_list) if authors_list else 'Unknown'

            article = Article(
                title=result['title'],
                authors=authors_str,
                summary=result['abstract'] or 'No abstract available.',
                pdf_url=result['pdf_url'] or '#',
                published=int(result['publication_year']) or -1,
                journal_ref=result['journal_name'] or 'No Journal available',  # Update if journal references are available
                cit_count=result["total_citations"],
                im_score=result["impact_score"]
            )
            new_results.append(article)
            # Update the results and is_searching flag inside async with self
            async with self:
                self.results = new_results
                self.original_results = new_results
                self.is_searching = False
                self.sort_date_mode = "default"

        return rx.toast.success(f"fetched {len(self.results)} articles!")

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
        
        async with self:
            self.clear_results()
            self.is_populating = False

        return rx.toast.success(f"Database populated with {num_articles_int} articles for query '{self.keywords}'.")
    



    @rx.event()
    def sort_by_date(self):
        self.reset_sort("date")
        """Sort the articles by date in ascending, descending, or original order."""
        # Helper function to parse the published date
        def parse_year(published_str):
            try:
                return int(published_str)
            except ValueError:
                return 0  # Use 0 for 'Unknown' or invalid years
                

        if self.sort_date_mode == "default":
            # First click: sort ascending
            self.sort_date_mode = "ascending"
            self.date_label = "Sort by date \u25bc"
            self.results = sorted(
                self.results,
                key=lambda article: parse_year(article.published)
            )
        elif self.sort_date_mode == "ascending":
            # Second click: sort descending
            self.sort_date_mode = "descending"
            self.date_label = "Sort by Date \u25b2"
            self.results = sorted(
                self.results,
                key=lambda article: parse_year(article.published),
                reverse=True
            )
        elif self.sort_date_mode == "descending":
            # Third click: return to original order
            self.sort_date_mode = "default"
            self.date_label = "Sort by Date"
            self.results = self.original_results.copy()

    @rx.event()
    def sort_by_citation(self):
        self.reset_sort("citation")
        """Sort the articles by date in ascending, descending, or original order."""
        # Helper function to parse the published date
        def parse_citation(citation_str):
            try:
                return int(citation_str)
            except ValueError:
                return 0  # Use 0 for 'Unknown' or invalid years
                

        if self.sort_citation_mode == "default":
            # First click: sort ascending
            self.sort_citation_mode = "ascending"
            self.citation_label = "Sort by Citations \u25bc"
            self.results = sorted(
                self.results,
                key=lambda article: parse_citation(article.cit_count)
            )
        elif self.sort_citation_mode == "ascending":
            # Second click: sort descending
            self.sort_citation_mode = "descending"
            self.citation_label = "Sort by Citations \u25b2"
            self.results = sorted(
                self.results,
                key=lambda article: parse_citation(article.cit_count),
                reverse=True
            )
        elif self.sort_citation_mode == "descending":
            # Third click: return to original order
            self.sort_citation_mode = "default"
            self.citation_label = "Sort by Citations"
            self.results = self.original_results.copy()

    @rx.event()
    def sort_by_score(self):
        self.reset_sort("score")
        """Sort the articles by date in ascending, descending, or original order."""
        # Helper function to parse the published date
        def parse_score(score_str):
            try:
                return float(score_str)
            except ValueError:
                return -1  # Use 0 for 'Unknown' or invalid years
                

        if self.sort_score_mode == "default":
            # First click: sort ascending
            self.sort_score_mode = "ascending"
            self.score_label = "Sort by Impact Score \u25bc"
            self.results = sorted(
                self.results,
                key=lambda article: parse_score(article.im_score)
            )
        elif self.sort_score_mode == "ascending":
            # Second click: sort descending
            self.sort_score_mode = "descending"
            self.score_label = "Sort by Impact Score \u25b2"
            self.results = sorted(
                self.results,
                key=lambda article: parse_score(article.im_score),
                reverse=True
            )
        elif self.sort_score_mode == "descending":
            # Third click: return to original order
            self.sort_score_mode = "default"
            self.score_label = "Sort by Impact Score"
            self.results = self.original_results.copy()

    def reset_sort(self, filter: str):
        if filter == "date":
            self.sort_citation_mode = "default"
            self.citation_label = "Sort by Citations"

            self.sort_score_mode = "default"
            self.score_label = "Sort by Impact Score"

        elif filter == "citation":
            self.sort_date_mode = "default"
            self.date_label = "Sort by Date"

            self.sort_score_mode = "default"
            self.score_label = "Sort by Impact Score"

        elif filter == "score":
            self.sort_citation_mode = "default"
            self.citation_label = "Sort by Citations"

            self.sort_date_mode = "default"
            self.date_label = "Sort by Date"


    @rx.var
    def privileged_email(self) -> bool:
        email = self.email
        return email in self.get_admins

    @rx.var
    def valid_buttons(self) -> list[str]:
        page_names: list[str] = ["/search"]

        if self.privileged_email:
            page_names += ["/admin", "/users"]
        try:
            page_names.remove(self.router_data["pathname"])
        except:
            pass
        return page_names


    @rx.var
    def no_results(self) -> bool:
        return self.is_searching or not self.original_results
     
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
        
    def on_login_success(self, id_token: dict):
        """Handle successful login and store the ID token."""
        self.id_token_json = json.dumps(id_token)
        if self.privileged_email:
            return rx.redirect("/admin")
        return rx.redirect("/search")
    
    def logout(self):
        """Log the user out by clearing the ID token."""
        self.id_token_json = ""
        self.clear_results()
        return rx.redirect("/")

    def unprivileged_redirect(self):
        if not self.privileged_email:
            return rx.redirect("/search")
        
    def on_login_page(self):
        if self.token_is_valid:
            return rx.redirect("/search")

    #export CSV functions
    @rx.event()
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