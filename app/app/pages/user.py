# this page is accesible to all users and displays the results from running the model 

# could use rx.spinner() to load data 

import reflex as rx
from ..state import State
from ..components import require_google_login, user_info, login

@rx.page(route="/user")
@require_google_login
def user_page() -> rx.Component:
    """The admin page where users can search for articles."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            user_info(State.tokeninfo),
            rx.heading("AFTAC: AI Driven R&D", size="2xl"),
            rx.text(
                "Enter keywords to find relevant research papers.",
                font_size="lg"
            ),
            # Input box for keyword search
            rx.input(
                placeholder="Enter keywords...",
                on_change=State.set_keywords,
                value=State.keywords,
                width="300px"
            ),
            
            rx.hstack(
                rx.input(
                    placeholder="Number of articles...",
                    on_change=State.set_num_articles,
                    value=State.num_articles,
                    width="300px",
                    type_="number",
                    min="1"
                ),
                rx.button(
                    "Search",
                    rx.spinner(loading=State.is_searching),
                    disabled=State.is_searching,
                    on_click=State.search_articles,
                    background_color="blue",
                    color="white",
                    padding="10px"
                ),
            ),

            rx.hstack(
                 rx.button(
                    "Clear Results",
                    on_click=State.clear_results,
                    disabled=State.is_searching,
                    background_color="blue",
                    margin_top="10px"
                ),
                rx.button(
                    "Export to CSV",
                    on_click=State.export_results_to_csv,
                    disabled=State.is_searching,
                    background_color="blue",
                    margin_top="10px"
                ),
                spacing="1"
            ),

            rx.hstack(
                 rx.button(
                    "Sort by citation count",
                    #on_click=State.clear_results,
                    disabled=State.is_searching,
                    background_color="green",
                    margin_top="10px"
                ),
                rx.button(
                    "Sort by date",
                    #on_click=State.export_results_to_csv,
                    disabled=State.is_searching,
                    background_color="green",
                    margin_top="10px"
                ),
                rx.button(
                    "Sort by impact score",
                    #on_click=State.export_results_to_csv,
                    disabled=State.is_searching,
                    background_color="green",
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
                )
            )
        )
    )
