import src.APIs.arXiv.arXiv_data as arxiv_api
import scripts.dbscript as script
import database.arxivdb as arxiv_db
import src.model.model as dl_model
from sklearn.feature_extraction.text import TfidfVectorizer

api_handler = arxiv_api.arxiv_api_handler()
results = api_handler.query("machine learning", 20)

filepath: str = "database/papers.sqlite"
script.create_database(filepath)
db_handler = arxiv_db.DBAccess(filepath)


for result in results:
    # print(result.title +", "+ str(result.published))
    # print(result.authors)
    # print(result.pdf_url)
    # print()
    db_handler.insert_paper(
        result.title,
        result.summary,
        result.published,
        result.journal_ref,
        pdf_url=result.pdf_url,
        doi=result.doi
    )



    # # Define the TF-IDF vectorizer and the relevance model
    # vectorizer = TfidfVectorizer()
    # model = dl_model.RelevanceModel(input_size=vectorizer.fit_transform(["test"]).shape[1], hidden_size=10)

    # # Example usage to get the most relevant articles based on keywords
    # keywords = "machine learning techniques"
    # relevant_papers = dl_model.get_most_relevant_articles(keywords, db_handler, model, vectorizer)

    # # Print the most relevant articles
    # for paper in relevant_papers:
    #     print(f"Title: {paper[1]}, Abstract: {paper[2]}")