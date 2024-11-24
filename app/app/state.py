import os
import re
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
from database.DatabaseManager import DatabaseManager
from database.populate_db import DatabaseSearchService

# to export csv
import csv
from io import StringIO

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')

G_db_manager: DatabaseManager = DatabaseManager()

class State(rx.State):
    # Google OAUTH token
    id_token_json: str = rx.LocalStorage()

    # shared between the admin and search pages
    keywords: str = ""
    num_articles: str = "" 
    results: list[Article] = []
    original_results: list[Article] = []

    # states to control button access in both search, users and admin pages
    is_searching: bool = False
    is_populating: bool = False
    is_removing: bool = False

    # sort states: default, ascending, descending
    sort_date_mode: str = "default"
    sort_score_mode: str = "default"
    sort_citation_mode: str = "default"
    
    # sorting labels
    date_label: str = "Sort by Date"
    citation_label: str = "Sort by Citations"
    score_label: str = "Sort by Impact Score"

    # admin entry field on users page
    admin_entry: str = ""

    

    """page redirect functions"""
    def go_admin_page(self):
        self.clear_results()
        return rx.redirect("/admin")

    def go_search(self):
        self.clear_results()
        return rx.redirect("/search")
    
    def go_users(self):
        self.clear_results()
        return rx.redirect("/users")

    # input validation for search, users, and admin pages
    def validate_input(self):
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

    def validate_email(self):
        if not self.admin_entry.strip():
            return rx.toast.warning("Admin field cannot be empty.")
        
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
        # Check if the provided email matches the regex
        if not re.match(email_regex, self.admin_entry.strip()):
            return rx.toast.warning("Invalid email format. Please enter a valid email address.")
        
        try:
            admins = [t[1] for t in G_db_manager.get_admins()]
        except Exception:
            return rx.toast.error("Failed to fetch admins from the database.")
        
        if self.admin_entry.strip() in admins:
            return rx.toast.error("Email already exists in the admin database.")
        
    # clears search results and resets input fields
    def clear_results(self):
        self.results = []
        self.original_results = []
        self.keywords = ""
        self.num_articles = ""
        self.admin_entry = ""
        self.reset_sort()

    @rx.event()
    def set_keywords(self, value: str):
        self.keywords = value

    @rx.event()
    def set_num_articles(self, value: str):
        self.num_articles = value

    @rx.event()
    def set_admin_entry(self, value: str):
        self.admin_entry = value
    
    
    #UI components functions
    @rx.event(background=True)
    async def search_articles(self):
        if a := self.validate_input(): return a

        async with self:
            self.is_searching = True
            start_time=time.time()
        
        num_articles_int = int(self.num_articles)

        rank_model = RankModel() # Get ranked articles from the model
        ranked_articles = rank_model.rank_articles(self.keywords, num_articles=num_articles_int)

        new_results = []  # build up a new list to store articles

        if ranked_articles.empty:
            async with self:
                self.results = []
                self.is_searching = False
                end_time=time.time()
            return rx.toast.error(f"No articles found for the given query in {(end_time - start_time):.2f} seconds.")

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
                journal_ref=result['journal_name'] or 'No Journal available',
                cit_count=int(result["total_citations"]),
                im_score=float(result["impact_score"])
            )
            new_results.append(article)

            # Update the results and is_searching flag
            async with self:
                self.results = new_results
                self.original_results = new_results
                self.is_searching = False
                end_time=time.time()
                self.reset_sort()
                

        return rx.toast.success(f"fetched {len(self.results)} articles in {(end_time - start_time):.2f} seconds!")

    @rx.event(background=True)
    async def populate_database(self):
        if a := self.validate_input(): return a

        num_articles_int = int(self.num_articles)
        if num_articles_int  > 100: 
            return rx.toast.warning("insert no more than 100 papers at a time")

        async with self:
            self.is_populating = True
            start_time= time.time()

        # Initialize the DatabaseSearchService with the query (keywords) and number of articles
        search_service = DatabaseSearchService(query=self.keywords, num_articles=(num_articles_int//4)) # we have 4 APIs... This is not the best way to do it
 
        search_service.search_and_store() # Run the search and store the results in the databases
        
        async with self:
            self.clear_results()
            self.is_populating = False
            end_time= time.time()

        return rx.toast.success(f"Database populated with {num_articles_int} articles for query '{self.keywords}' in {(end_time - start_time):.2f} seconds.")
    

    """users page functions"""
    @rx.event(background=True)
    async def add_admin(self):
        
        if a := self.validate_email(): return a

        async with self:
            self.is_populating = True
            start_time= time.time()

        try:
            G_db_manager.insert_admin(self.admin_entry)
        except Exception:
            self.is_populating = False
            return rx.toast.error(f"failed to insert {self.admin_entry} as an admin")
        

        async with self:
            self.clear_results()
            self.is_populating = False
            end_time= time.time()

        return rx.toast.success(f"inserted {self.admin_entry} as an admin within {(end_time - start_time):.2f} seconds")

    @rx.event(background=True)
    async def remove_admin(self, email: str):

        email = email.strip()
        if email == self.tokeninfo["email"]:
            return rx.toast.error("cannot remove self as admin")
        
        try:
            admin_count = len(G_db_manager.get_admins())
        except Exception:
            return rx.toast.error("Failed to fetch admins from the database.")
        
        if admin_count <= 4:
            return rx.toast.error("there must be a minimum of four admins")

        async with self:
            self.is_removing = True
            start_time= time.time()
        try:
            G_db_manager.remove_admin(email)
        except Exception:
            self.is_removing = False
            return rx.toast.error(f"failed to remove {email} from admins")

        async with self:
            self.is_removing = False
            end_time= time.time()

        return rx.toast.success(f"removed {email} as an admin within {(end_time - start_time):.2f} seconds")

    @rx.var
    def get_admins(self) -> list[str]:
        try:
            return [t[1] for t in G_db_manager.get_admins()]
        except Exception:
            return rx.toast.error("Failed to display admins")
    

    """sort functionality on search page"""
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

    def reset_sort(self, filter: str = None):
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

        else:
            self.sort_citation_mode = "default"
            self.citation_label = "Sort by Citations"

            self.sort_score_mode = "default"
            self.score_label = "Sort by Impact Score"

            self.sort_date_mode = "default"
            self.date_label = "Sort by Date"

    @rx.var
    def database_running(self) -> bool:
        return self.is_searching or self.is_populating

    @rx.var
    def no_results(self) -> bool:
        return self.is_searching or not self.original_results
     
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
    
    
    """Google OAUTH functions"""
    @rx.var(cache=True) # extracts the user's email from tokeninfo.
    def email(self) -> str:
        # access the reactive tokeninfo variable
        tokeninfo = self.tokeninfo  

        # af tokeninfo exists and has an 'email' key, return it, otherwise return an empty string
        return tokeninfo["email"] if "email" in tokeninfo else ""

    @rx.var
    def privileged_email(self) -> bool:
        email = self.email
        return email in self.get_admins
    
    @rx.var(cache=True) # verifies and parses the user's ID token.
    def tokeninfo(self) -> dict[str, str]:
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

    @rx.var # checks if the user's token is valid
    def token_is_valid(self) -> bool:
        try:
            return bool(
                self.tokeninfo
                and int(self.tokeninfo.get("exp", 0))
                > time.time()
            )
        except Exception:
            return False
       
    # handles successful login and stores the ID token
    def on_login_success(self, id_token: dict):
        self.id_token_json = json.dumps(id_token)
        if self.privileged_email:
            return rx.redirect("/admin")
        return rx.redirect("/search")
    
    # log the user out by clearing the ID token
    def logout(self):
        self.id_token_json = ""
        self.clear_results()
        return rx.redirect("/")

    def unprivileged_redirect(self):
        if not self.privileged_email:
            return rx.redirect("/search")
        
    def on_login_page(self):
        if self.token_is_valid:
            return rx.redirect("/search")
    

    """export CSV functions"""
    @rx.event() # export search results to a CSV with title, authors, pdf, and published date.
    def export_results_to_csv(self):
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