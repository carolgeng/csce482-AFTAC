import reflex as rx
from ..state import State
from ..components import require_google_login, navigation_bar, require_privilege

@rx.page(route="/users")
@require_google_login
@require_privilege
def users_page() -> rx.Component:
    """The admin page where users can search for articles."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.hstack(
                navigation_bar(State.tokeninfo)
            ),

            rx.vstack(
                rx.hstack(
                    rx.input(
                        placeholder="Enter admin email...",
                        on_change=State.set_admin_entry,
                        # value=State.admin_entry,
                        width="300px"
                    ),
                    rx.button(
                        "add admin",
                        on_click=State.add_admin
                    )
                ),
                rx.vstack(
                    rx.foreach(
                        State.get_admins,
                        lambda admin: rx.hstack(
                            rx.button(
                                "Remove",
                                on_click=State.remove_admin(admin)
                            ),
                            rx.text(admin),
                            
                        )
                    )
                )
            )
        )
    )