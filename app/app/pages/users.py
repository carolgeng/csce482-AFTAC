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
                rx.vstack(
                    navigation_bar(State.tokeninfo),
                    rx.text(
                        "Enter single email at a time to give admin access",
                        font_size="lg"
                    )
                ),
            ),

            rx.vstack(
                rx.hstack(
                    rx.input(
                        placeholder="Enter admin email...",
                        on_change=State.set_admin_entry,
                        value=State.admin_entry,
                        width="300px"
                    ),
                    rx.button(
                        "add admin",
                        rx.spinner(loading=State.database_running),
                        background_color="blue",
                        color="white",
                        disabled=State.database_running,
                        on_click=State.add_admin
                    )
                ),
                rx.vstack(
                    rx.foreach(
                        State.get_admins,
                        lambda admin: rx.hstack(
                            rx.button(
                                "Remove",
                                rx.spinner(loading=State.is_removing),
                                background_color="blue",
                                disabled=State.is_removing,
                                on_click=State.remove_admin(admin)
                            ),
                            rx.text(admin),
                            
                        )
                    )
                )
            )
        )
    )