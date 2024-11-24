import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class api_handler:
    def __init__(self, api_key=None):
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.fields = [
            "title",
            "authors",
            "year",
            "abstract",
            "externalIds",
            "url",
            "influentialCitationCount"
        ]  # Fields to include in the API response
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def query(self, query, max_results=None):
        params = {
            "query": query,
            "fields": ",".join(self.fields),
            "limit": max_results if max_results else 100  # Semantic Scholar allows up to 100 results per request
        }

        try:
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()  # Raise an error if the request fails
            data = response.json()
            
            if "data" in data:
                for paper in data["data"]:
                    if paper.get("externalIds", {}).get("DOI"):  # Only yield papers with a DOI
                        yield paper
            else:
                print("No data found in the response.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while querying Semantic Scholar: {e}")
        except ValueError as e:
            print(f"An error occurred while parsing the response: {e}")

# # Example usage
# if __name__ == "__main__":
#     # Load the API key from the .env file
#     api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
#     if not api_key:
#         print("Error: API key not found. Please set SEMANTIC_SCHOLAR_API_KEY in your .env file.")
#     else:
#         handler = api_handler(api_key=api_key)
#         for result in handler.query("machine learning", max_results=5):
#             print(result.get("externalIds", {}).get("DOI"), result.get("title", "No Title"))
