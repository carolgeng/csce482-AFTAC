import reflex as rx
from ..state import State
from ..components import require_google_login, navigation_bar

@rx.page(route="/users")
@require_google_login
def users_page() -> rx.Component:
    """The admin page where users can search for articles."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.hstack(
                navigation_bar(State.tokeninfo)
            ),
        )
    )