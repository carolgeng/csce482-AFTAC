# this page is the root page with welcome text and login w/ google button

import reflex as rx
from ..state import State
from ..components import login, require_google_login

@rx.page(route="/")
@require_google_login
def login_page() -> rx.Component:
    """The login page with just the welcome to the app text box and the sign in with google button."""
    return rx.container(
        rx.vstack(
            rx.color_mode.button(position="top-right"),
            rx.heading("Welcome to the AFTAC: AI Driven R&D App", size="lg"),
            rx.text("Please sign in with Google to continue.", size="md", padding="10px"),
            login()

        ),
        padding="20px",
    )