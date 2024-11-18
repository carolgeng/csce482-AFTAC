import reflex as rx
from .state import State
from .react_oauth_google import (
    GoogleOAuthProvider,
    GoogleLogin,
)
import functools
from dotenv import load_dotenv
import os

# gets client id from env file
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')

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
