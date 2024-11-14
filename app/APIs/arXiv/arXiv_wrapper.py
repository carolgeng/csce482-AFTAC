import arxiv
from arxiv import UnexpectedEmptyPageError

class api_handler:
    
    def __init__(self):
        self.client = arxiv.Client()

    def query(self, query, max_results=None):
        search = arxiv.Search(
            query=query,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending
        )
        # Generator function to yield results with a DOI
        def results_with_doi():
            count = 0
            try:
                for result in self.client.results(search):
                    if result.doi:
                        yield result
                        count += 1
                        if max_results is not None and count >= max_results:
                            break
            except UnexpectedEmptyPageError as e:
                print(f"Unexpected empty page encountered: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")
        return results_with_doi()
