import reflex as rx
from ..state import State
from ..components import login
from ..react_oauth_google import GoogleOAuthProvider
import os

@rx.page(route="/")
def login_page() -> rx.Component:
    """The login page with welcome text and Google sign-in button."""
    return GoogleOAuthProvider.create(
        rx.center(
            rx.color_mode.button(position="top-right"),
            rx.card(
                rx.heading(
                    "Welcome to AI Driven R&D!", 
                    size="6",  # Larger heading
                    text_align="center",
                    padding="0.5em"
                ),
                
                rx.text(
                    "Please sign in with Google to continue.",
                    size="5",  # Larger text for instructions
                    text_align="center",
                    margin_bottom="1.5em",
                ),
                rx.vstack(
                    login(),
                    align="center",
                    spacing="2",
                    size="xl"  # Increased spacing for better balance
                ),
                padding="4em",  # More padding for an airy layout
                border_radius="20px",  # Larger corner radius for a modern look
                bg="gray.800",  # Solid dark background

                box_shadow="2xl",  # Extra shadow for emphasis
                max_width="700px",  # Wider card
                width="90%",  # Responsive width
            ),
            height="100vh",  # Full viewport height for centering
            bg="gray.200",  # Light background for contrast
        ),
        client_id=os.getenv("CLIENT_ID"),
    )
