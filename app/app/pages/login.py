# this page is the root page with welcome text and login w/ google button

import reflex as rx
from ..state import State
from ..components import login
from ..react_oauth_google import (
    GoogleOAuthProvider
)
import os

@rx.page(route="/")
def login_page() -> rx.Component:
    """The login page with just the welcome to the app text box and the sign in with google button."""
    return GoogleOAuthProvider.create(
        rx.container(
            rx.vstack(
                rx.heading("Welcome to the AFTAC: AI Driven R&D App", size="lg"),
                rx.text("Please sign in with Google to continue.", size="md", padding="10px"),
                login(),  
            ),
            padding="20px",
        ),
        client_id=os.getenv('CLIENT_ID'),
    )