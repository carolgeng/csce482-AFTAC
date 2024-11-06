import reflex as rx
from rxconfig import config
from APIs.arXiv.arXiv_wrapper import api_handler

class Article(rx.Base):
    title: str
    authors: str
    summary: str
    pdf_url: str

class State(rx.State):
    """The app state."""
    # Store the user's input keywords
    keywords: str = ""
    # Store the user's desired number of articles as a string
    num_articles: str = "10"  # Default value
    # Store the search results as a list of Article models
    results: list[Article] = []

    def search_articles(self):
        """Function to handle article search."""
        handler = api_handler()
        # Convert num_articles to int
        try:
            num_articles_int = int(self.num_articles)
        except ValueError:
            num_articles_int = 10  # Default or handle error
        # Get the generator of results
        results_generator = handler.query(self.keywords, num_articles_int)
        # Extract relevant information from the results
        self.results = [
            Article(
                title=result.title,
                authors=', '.join([author.name for author in result.authors]),
                summary=result.summary,
                pdf_url=result.pdf_url,
            )
            for result in results_generator
        ]

    def set_num_articles(self, value):
        """Set the number of articles."""
        self.num_articles = value

    def clear_results(self):
        """Clear the search results and reset input fields."""
        self.results = []
        self.keywords = ""
        self.num_articles = "10"

def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("AFTAC: AI Driven R&D", size="9"),
            rx.text("Enter keywords to find relevant articles.", size="5"),
            # Input field for keywords
            rx.input(
                placeholder="Enter keywords...",
                on_change=State.set_keywords,
                value=State.keywords,
                width="300px"
            ),
            # Input field for number of articles
            rx.input(
                placeholder="Number of articles...",
                on_change=State.set_num_articles,
                value=State.num_articles,
                width="300px",
                type_="number",
                min="1"
            ),
            # Buttons container
            rx.hstack(
                # Search button
                rx.button(
                    "Search",
                    on_click=State.search_articles,
                    margin_top="10px"
                ),
                # Clear Results button
                rx.button(
                    "Clear Results",
                    on_click=State.clear_results,
                    margin_top="10px"
                ),
                spacing="10px"
            ),
            # Display results
            rx.vstack(
                rx.foreach(
                    State.results,
                    lambda result: rx.box(
                        rx.heading(result.title, size="md"),
                        rx.text("Authors: " + result.authors),
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

app = rx.App()
app.add_page(index)
