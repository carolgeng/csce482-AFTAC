import requests

class api_handler:
    def __init__(self):
        self.base_url = "https://api.crossref.org/works"

    def query(self, query, max_results=None):
        params = {
            "query": query,
            "rows": max_results if max_results else 1000  # Use the maximum allowed by CrossRef
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            if "message" in data and "items" in data["message"]:
                for item in data["message"]["items"]:
                    if "DOI" in item:
                        yield item
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while querying CrossRef: {e}")

# # Example usage
# if __name__ == "__main__":
#     handler = api_handler()
#     for result in handler.query("machine learning", max_results=5):
#         print(result.get("DOI"), result.get("title", ["No Title"])[0])
