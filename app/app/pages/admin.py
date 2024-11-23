# this page is the one that is only for AFTAC/TAMU users to retrain the model and repopulate the db

import reflex as rx
from ..state import State
from ..components import require_google_login, user_info, login

@rx.page(route="/admin")
@require_google_login
def admin_page() -> rx.Component:
    """The admin page where users can search for articles."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("AFTAC: AI Driven R&D", size="2xl"),
            rx.text(
                "Enter keywords to populate the database.",
                font_size="lg"
            ),
            # Input box for keyword search
            rx.input(
                placeholder="Enter keywords...",
                on_change=State.set_keywords,
                value=State.keywords,
                width="300px"
            ),
            # Input box for number of articles
            rx.input(
                placeholder="Number of articles...",
                on_change=State.set_num_articles,
                value=State.num_articles,
                width="300px",
                type_="number",
                min="1"
            ),
            rx.hstack(
                rx.button(
                    "Populate Database",
                    rx.spinner(loading=State.is_populating),
                    disabled=State.is_busy,
                    background_color="blue",
                    color=State.populate_button_color,
                    on_click=State.populate_database,
                    margin_top="10px"
                ),
                rx.button(
                    "Retrain Model",
                    rx.spinner(loading=State.is_training),
                    disabled=State.is_busy,
                    background_color="green",
                    color=State.retrain_button_color,
                    on_click=State.retrain_model,
                    margin_top="10px"
                ),
            ),
            rx.hstack(
                rx.button(
                    "Back",
                    disabled=State.is_busy,
                    background_color="red",
                    on_click=State.go_back,
                    margin_top="10px"
                ),
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
                            spacing="1",
                        ),
                        rx.hstack(
                            rx.text("Published: ", font_weight="bold"),
                            rx.text(result.published),
                            spacing="1",
                        ),
                        rx.cond(
                            result.journal_ref != "",
                            rx.hstack(
                                rx.text("Journal Reference: ", font_weight="bold"),
                                rx.text(result.journal_ref),
                                spacing="1",
                            ),
                            rx.hstack(
                                rx.text("Journal Reference: ", font_weight="bold"),
                                rx.text("No journal reference"),
                                spacing="1",
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