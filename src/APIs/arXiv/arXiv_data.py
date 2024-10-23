import arxiv

class arxiv_api_handler:
    def __init__(self):
        self.client = arxiv.Client()

    def query(self, query, max_results):
        search = arxiv.Search(
            query,
            max_results = max_results,
            sort_by= arxiv.SortCriterion.Relevance
        )
        return self.client.results(search)
