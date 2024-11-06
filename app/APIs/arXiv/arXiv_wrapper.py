import arxiv

class api_handler:
    
    def __init__(self):
        self.client = arxiv.Client()

    def query(self, query, max_results):
        search = arxiv.Search(
            query=query,
            sort_by=arxiv.SortCriterion.Relevance
        )
        # Generator function to yield results with a DOI
        def results_with_doi():
            count = 0
            for result in self.client.results(search):
                if result.doi:
                    yield result
                    count += 1
                    if count >= max_results:
                        break
        return results_with_doi()
