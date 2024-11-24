# app/APIs/open_alex/open_alex_wrapper.py

import requests

class OpenAlexAPIHandler:
    def __init__(self):
        # No specialized client initialization is required for OpenAlex.
        pass

    def query(self, query_string, max_results=None):
        """
        Query the OpenAlex API for works matching the given query string,
        optionally limiting the number of results.

        Parameters:
            query_string (str): The search query to use.
            max_results (int, optional): The maximum number of results to yield.
                Defaults to None, meaning no limit.

        Returns:
            generator: A generator that yields results from the OpenAlex API.
        """
        def results_generator():
            count = 0
            cursor = '*'
            per_page = 200  # Maximum per-page limit for OpenAlex API

            while True:
                url = 'https://api.openalex.org/works'
                headers = {'User-Agent': 'YourAppName (your_email@example.com)'}
                params = {
                    'search': query_string,
                    'per-page': per_page,
                    'cursor': cursor,
                    'sort': 'cited_by_count:desc'
                }
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    results = data.get('results', [])

                    if not results:
                        break

                    for work in results:
                        yield work
                        count += 1
                        if max_results is not None and count >= max_results:
                            return

                    cursor = data.get('meta', {}).get('next_cursor')
                    if not cursor:
                        break
                except requests.RequestException as e:
                    print(f"An error occurred: {e}")
                    break

            return

        return results_generator()
