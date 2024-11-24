import os
import functools
import reflex as rx
from dotenv import load_dotenv

from .state import State
from .react_oauth_google import (
    GoogleOAuthProvider,
    GoogleLogin,
)

# gets client id from env file
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')

# Google OAUTH components
def navigation_bar(self) -> rx.Component:
    """Display the user's information, including avatar and email."""
    return rx.vstack(
        rx.heading("AFTAC: AI Driven R&D", size="2xl"),
        rx.hstack(
            rx.button(
                "Logout", 
                on_click=State.logout,
                disabled=State.is_searching,
                background_color="grey"
            ),
            rx.foreach(
                State.valid_buttons,
                lambda button: rx.vstack(
                    rx.cond(
                        button == "/search",
                        rx.button(
                            "Search",
                            disabled=State.is_busy,
                            background_color="red",
                            on_click=State.go_search,
                        )
                    ),
                    rx.cond(
                        button == "/admin",
                        rx.button(
                            "Admin",
                            disabled=State.is_searching,
                            on_click=State.go_admin_page,
                            background_color="red",
                            padding="10px"
                        )
                    ),
                    rx.cond(
                        button == "/users",
                        rx.button(
                            "Users",
                            disabled=State.is_searching,
                            on_click=State.go_users,
                            background_color="red",
                            padding="10px"
                        )
                    )
                )
            )
        )
    )

def login() -> rx.Component:
    """Display the Google Login button."""
    return rx.vstack(
        GoogleLogin.create(on_success=State.on_login_success),
    )

def require_google_login(page) -> rx.Component:
    """Ensure that the user is logged in before accessing the page."""
    @functools.wraps(page)
    def _auth_wrapper() -> rx.Component:
        return GoogleOAuthProvider.create(
            rx.cond(
                State.is_hydrated,
                rx.cond(
                    State.token_is_valid,
                    page(),
                    rx.button("Go back.", on_click=lambda: rx.redirect("/")),
                ),
                # nothing
            ),
            client_id=CLIENT_ID,
        )

    return _auth_wrapper

# UI Components
def require_privilege(page) -> rx.Component:
    @functools.wraps(page)
    def _auth_wrapper() -> rx.Component:
        return rx.cond(
            State.privileged_email,
            page(),
            rx.button("Go back.", on_click=lambda: rx.redirect("/")),
        )
    return _auth_wrapper