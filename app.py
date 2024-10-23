import src.APIs.arXiv.arXiv_data as arxiv_api

handler = arxiv_api.arxiv_api_handler()

results = handler.query("machine learning", 20)

for result in results:
    print(result.title +", "+ str(result.published))
    print(result.authors)
    print(result.pdf_url)
    print()