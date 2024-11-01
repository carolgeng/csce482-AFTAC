import sqlite3
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from sklearn.feature_extraction.text import TfidfVectorizer

class RelevanceModel(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(RelevanceModel, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, 1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = torch.sigmoid(self.fc2(x))
        return x
    
def get_most_relevant_articles(keywords, db_access, model, vectorizer):
    # Fetch all papers from the database
    papers = db_access.fetch_papers()

    # Extract abstracts for TF-IDF vectorization
    abstracts = [paper[2] for paper in papers]

    # Convert the keywords and abstracts to TF-IDF vectors
    abstracts_tfidf = vectorizer.fit_transform(abstracts)
    keywords_tfidf = vectorizer.transform([keywords])

    # Convert TF-IDF vectors to tensors
    abstracts_tensor = torch.tensor(abstracts_tfidf.toarray(), dtype=torch.float32)
    keywords_tensor = torch.tensor(keywords_tfidf.toarray(), dtype=torch.float32)

    # Calculate relevance scores
    relevance_scores = model(abstracts_tensor @ keywords_tensor.T).squeeze()

    # Sort papers by relevance score
    sorted_indices = torch.argsort(relevance_scores, descending=True)
    most_relevant_papers = [papers[i] for i in sorted_indices]

    return most_relevant_papers



