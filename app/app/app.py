# for oauth
import functools
import json
import os
import time
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
from .react_oauth_google import (
    GoogleOAuthProvider,
    GoogleLogin,
)
from dotenv import load_dotenv

# to export csv
import csv
from io import StringIO

# for article serach app
import reflex as rx
from datetime import datetime
from rxconfig import config
from APIs.arXiv.arXiv_wrapper import api_handler
from datetime import datetime

# for model
from model.RankModel import RankModel

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
        """Function to handle article search and ranking."""
        try:
            num_articles_int = int(self.num_articles)
        except ValueError:
            num_articles_int = 10  # Default or handle error

        rank_model = RankModel()
        # Get ranked articles from the model
        ranked_articles = rank_model.rank_articles(self.keywords, num_articles=num_articles_int)
        
        # Initialize an empty list to store articles
        self.results = []
        if ranked_articles.empty:
            print("No articles found for the given query.")
            return

        for _, result in ranked_articles.iterrows():
            # Filter out None values in authors
            authors_list = [a for a in result['authors'] if a] if result['authors'] else []
            authors_str = ', '.join(authors_list) if authors_list else 'Unknown'
            
            # Create Article instance
            article = Article(
                title=result['title'],
                authors=authors_str,
                summary=result['abstract'] or 'No abstract available.',
                pdf_url=result['pdf_url'] or '#',
                published=str(result['publication_year']) or 'Unknown',
                comment="",  # You can update this if comments are available
                journal_ref="",  # Update if journal references are available
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



def user_info(tokeninfo: dict) -> rx.Component:
    """Display the user's information, including avatar and email."""
    return rx.hstack(
        rx.avatar(
            name=tokeninfo["name"],
            src=tokeninfo["picture"],
            size="md",
        ),
        rx.vstack(
            rx.heading(tokeninfo["name"], size="md"),
            rx.text(tokeninfo["email"]),
            align_items="flex-start",
        ),
        rx.button("Logout", on_click=State.logout),
        padding="10px",
    )


def login() -> rx.Component:
    """Display the Google Login button."""
    return rx.vstack(
        GoogleLogin.create(on_success=State.on_success),
    )


def require_google_login(page) -> rx.Component:
    """Ensure that the user is logged in before accessing the page."""
    @functools.wraps(page)
    def _auth_wrapper() -> rx.Component:
        return GoogleOAuthProvider.create(
            rx.cond(
                State.is_hydrated,
                rx.cond(
                    State.token_is_valid, page(), login()
                ),
                rx.spinner(),
            ),
            client_id=CLIENT_ID,
        )

    return _auth_wrapper


@rx.page(route="/")
@require_google_login
def protected() -> rx.Component:
    """The protected page where users can search for articles."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            user_info(State.tokeninfo),
            rx.heading("AFTAC: AI Driven R&D", size="2xl"),
            rx.text(
                "Enter keywords to find relevant articles.",
                font_size="lg"
            ),
            # input box for keyword search
            rx.input(
                placeholder="Enter keywords...",
                on_change=State.set_keywords,
                value=State.keywords,
                width="300px"
            ),
            # input box for num of articles
            rx.input(
                placeholder="Number of articles...",
                on_change=State.set_num_articles,
                value=State.num_articles,
                width="300px",
                type_="number",
                min="1"
            ),                
            rx.button(
                    "Search",
                    on_click=State.search_articles,
                    margin_top="10px"
            ),
            rx.hstack(
                rx.button(
                    "Clear Results",
                    on_click=State.clear_results,
                    margin_top="10px"
                ),
                rx.button(
                    "Export to CSV",
                    on_click=State.export_results_to_csv,
                    margin_top="10px"
                ),
                spacing="1"  
            ),

            # display results
            rx.vstack(
                rx.foreach(
                    State.results,
                    lambda result: rx.box(
                        rx.heading(result.title, size="md"),
                        rx.hstack(
                            rx.text("Authors: ", font_weight="bold"),
                            rx.text(result.authors),
                            spacing="1",
                        ),
                        rx.hstack(
                            rx.text("Published: ", font_weight="bold"),
                            rx.text(result.published),
                            spacing="1",
                        ),
                        rx.cond(
                            result.comment != "",
                            rx.hstack(
                                rx.text("Comments: ", font_weight="bold"),
                                rx.text(result.comment),
                                spacing="1",
                            ),
                            rx.hstack(
                                rx.text("Comments: ", font_weight="bold"),
                                rx.text("No comments"),
                                spacing="1",
                            )
                        ),
                        rx.cond(
                            result.journal_ref != "",
                            rx.hstack(
                                rx.text("Journal Reference: ", font_weight="bold"),
                                rx.text(result.journal_ref),
                                spacing="1",
                            ),
                            rx.hstack(
                                rx.text("Journal Reference: ", font_weight="bold"),
                                rx.text("No journal reference"),
                                spacing="1",
                            )
                        ),
                        rx.text(result.summary),
                        rx.link(
                            "Download PDF",
                            href=result.pdf_url,
                            is_external=True,
                            color="blue.500",
                            text_decoration="underline"
                        ),
                        margin_bottom="10px",
                        padding="10px",
                        border="1px solid #ccc",
                        border_radius="5px"
                    )
                ),
                spacing="2",
                align_items="start",
                margin_top="20px"
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
    )


app = rx.App()
