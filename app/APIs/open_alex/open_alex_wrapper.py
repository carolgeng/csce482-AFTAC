import requests

class openalex_api_handler:
    def __init__(self):
        # No specialized client initialization is required for OpenAlex.
        pass

    def query(self, query, max_results=None):
        """
        Query the OpenAlex API for works matching the given query string, optionally limiting the number of results.

        Parameters:
            query (str): The search query to use.
            max_results (int, optional): The maximum number of results to yield. Defaults to None, meaning no limit.

        Returns:
            generator: A generator that yields results from the OpenAlex API.
        """
        # Generator function to yield results
        def results_generator():
            count = 0
            page = 1
            per_page = 50  # Number of results per page
            while True:
                url = f"https://api.openalex.org/works?search={query}&per-page={per_page}&page={page}&sort=cited_by_count:desc"
                try:
                    response = requests.get(url)
                    response.raise_for_status()  # Raise HTTPError if the request was not successful
                    data = response.json()

                    # Extract the list of works from the response
                    works = data.get("results", [])

                    # If no works are returned, we've likely reached the end of results
                    if not works:
                        break

                    for work in works:
                        yield work
                        count += 1
                        if max_results is not None and count >= max_results:
                            return

                    page += 1  # Move to the next page of results

                except requests.RequestException as e:
                    print(f"An error occurred: {e}")
                    break

        return results_generator()

if __name__ == "__main__":
    # Create an instance of the handler
    handler = openalex_api_handler()
    
    # Sample query
    query_string = "quantum computing"
    max_results = 5  # We'll limit the results for demonstration

    print(f"Querying OpenAlex for '{query_string}' and retrieving up to {max_results} results...")

    # Get the generator for query results
    results_generator = handler.query(query_string, max_results)

    # Iterate over the returned results and print them out
    for i, result in enumerate(results_generator, start=1):
        title = result.get('title', 'No Title')
        openalex_id = result.get('id', 'No ID')
        doi = result.get('doi', 'No DOI')
        print(f"\nResult {i}:")
        print(f"  Title: {title}")
        print(f"  OpenAlex ID: {openalex_id}")
        print(f"  DOI: {doi}")
