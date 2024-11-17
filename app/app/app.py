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

# for article serach app
import reflex as rx
from datetime import datetime
from rxconfig import config
from APIs.arXiv.arXiv_wrapper import api_handler
from datetime import datetime

import reflex as rx

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
            self.results.append(article)

    def clear_results(self):
        """Clear the search results and reset input fields."""
        self.results = []
        self.keywords = ""
        self.num_articles = "10"

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
        # Use the standard button to toggle color mode
        # Use the standard button to toggle color mode
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            user_info(State.tokeninfo),
            rx.heading("AFTAC: AI Driven R&D", size="2xl"),
            rx.text(
                "Enter keywords to find relevant articles.",
                font_size="lg"
            ),
            # Input field for keywords
            rx.input(
                placeholder="Enter keywords...",
                on_change=State.set_keywords,
                value=State.keywords,
                width="300px"
            ),
            # Input field for number of articles
            rx.input(
                placeholder="Number of articles...",
                on_change=State.set_num_articles,
                value=State.num_articles,
                width="300px",
                type_="number",
                min="1"
            ),
            # Buttons container
            rx.hstack(
                # Search button
                rx.button(
                    "Search",
                    on_click=State.search_articles,
                    margin_top="10px"
                ),
                # Clear Results button
                rx.button(
                    "Clear Results",
                    on_click=State.clear_results,
                    margin_top="10px"
                ),
                spacing="10px"
            ),
            # Display results
            rx.vstack(
                rx.foreach(
                    State.results,
                    lambda result: rx.box(
                        rx.heading(result.title, size="md"),
                        rx.hstack(
                            rx.text("Authors: ", font_weight="bold"),
                            rx.text(result.authors),
                            spacing="0px",
                        ),
                        rx.hstack(
                            rx.text("Published: ", font_weight="bold"),
                            rx.text(result.published),
                            spacing="0px",
                        ),
                        rx.cond(
                            result.comment != "",
                            rx.hstack(
                                rx.text("Comments: ", font_weight="bold"),
                                rx.text(result.comment),
                                spacing="0px",
                            ),
                            rx.hstack(
                                rx.text("Comments: ", font_weight="bold"),
                                rx.text("No comments"),
                                spacing="0px",
                            )
                        ),
                        rx.cond(
                            result.journal_ref != "",
                            rx.hstack(
                                rx.text("Journal Reference: ", font_weight="bold"),
                                rx.text(result.journal_ref),
                                spacing="0px",
                            ),
                            rx.hstack(
                                rx.text("Journal Reference: ", font_weight="bold"),
                                rx.text("No journal reference"),
                                spacing="0px",
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

