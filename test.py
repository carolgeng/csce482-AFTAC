import requests
import json
import gzip
import os

# Make sure your API key is set
API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
DATASET_NAME = "s2orc"

# Get the latest release
response = requests.get("https://api.semanticscholar.org/datasets/v1/release/latest").json()
RELEASE_ID = response["release_id"]
print(f"Latest release ID: {RELEASE_ID}")

# Get download links for the dataset
response = requests.get(f"https://api.semanticscholar.org/datasets/v1/release/{RELEASE_ID}/dataset/{DATASET_NAME}/",
                        headers={"x-api-key": API_KEY}).json()

# Let's get the first file URL to inspect
url = response["files"][0]
print(f"Inspecting file URL: {url}")

# Download and inspect the first few lines of the Gzipped data
r = requests.get(url, stream=True)

line_count = 0

# Open the Gzipped file from the stream and read lines
with gzip.GzipFile(fileobj=r.raw) as f:
    for line in f:
        paper_data = json.loads(line.decode('utf-8'))  # Decode each line from bytes
        print(json.dumps(paper_data, indent=4))  # Pretty print JSON
        line_count += 1
        if line_count >= 5:  # Stop after inspecting the first 5 papers
            break
