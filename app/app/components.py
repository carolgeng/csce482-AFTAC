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

def user_info(self) -> rx.Component:
    """Display the user's information, including avatar and email."""
    email = self.email 
    return rx.hstack(
        
        rx.button(
            "Logout", 
            on_click=State.logout,
            disabled=State.is_searching,
            background_color="grey"
        ),
        rx.cond(
            # we can add AFTAC here
            (email != "") & ((email == "mev@tamu.edu") | (email == "sulaiman_1@tamu.edu") | (email == "sryeruva@tamu.edu") | (email == "alecklem@tamu.edu") ),  
            rx.button(
                "Admin Page",
                disabled=State.is_searching,
                on_click=lambda: rx.redirect("/admin"),
                background_color="red",
                padding="10px",
            ),
            rx.text(""),  
        ),
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
