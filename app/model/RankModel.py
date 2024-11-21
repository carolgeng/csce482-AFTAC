import os
import psycopg2
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..database.DatabaseManager import DatabaseManager
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler


class RankModel:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.database_url = os.getenv('DATABASE_URL')
        self.connection = psycopg2.connect(self.database_url)
        self.db_manager = DatabaseManager()
        self.model = self.load_model()

    def load_model(self):
        model_file = 'ml_model.pkl'
        if os.path.exists(model_file):
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            print("Loaded existing ML model.")
        else:
            print("Training new ML model...")
            model = self.train_ml_model()
        return model

    def train_ml_model(self):
        # Fetch articles data from the database
        articles = self.get_articles_from_db()

        # Select relevant features for impact prediction
        features = articles[[
            'publication_year',
            'delta_citations',
            'journal_h_index',
            'mean_citations_per_paper',
            'total_papers_published',
            'num_authors',
            'avg_author_h_index',
            'avg_author_total_papers',
            'avg_author_total_citations',
            'total_citations'
        ]]
        target = articles['influential_citations']  # Assuming total citations as impact

        # Handle missing values
        features = features.fillna(0)
        target = target.fillna(0)

        # Split data into training and testing sets
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

        # Train a RandomForestRegressor model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # After training the model
        feature_importances = model.feature_importances_
        for name, importance in zip(features, feature_importances):
            print(f"Feature: {name}, Importance: {importance}")

        # Evaluate the model
        from sklearn.metrics import mean_squared_error
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"Model Mean Squared Error: {mse}")

        # Save the trained model to a file
        with open('ml_model.pkl', 'wb') as f:
            pickle.dump(model, f)

        return model

    def get_articles_from_db(self):
        # Fetch articles and related data from the database
        query = """
            SELECT
                p.id,
                p.title,
                p.abstract,
                p.total_citations,
                p.influential_citations,
                p.publication_year,
                p.delta_citations,
                p.pdf_url,
                j.journal_h_index,
                j.mean_citations_per_paper,
                j.total_papers_published,
                COUNT(pa.author_id) AS num_authors,
                AVG(a.h_index) AS avg_author_h_index,
                AVG(a.total_papers) AS avg_author_total_papers,
                AVG(a.total_citations) AS avg_author_total_citations,
                array_agg(a.name) FILTER (WHERE a.name IS NOT NULL) AS authors
            FROM papers p
            LEFT JOIN journals j ON p.journal_id = j.id
            LEFT JOIN paper_authors pa ON p.id = pa.paper_id
            LEFT JOIN authors a ON pa.author_id = a.id
            GROUP BY p.id, j.journal_h_index, j.mean_citations_per_paper, j.total_papers_published
        """
        try:
            with self.connection.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                articles = pd.DataFrame(rows, columns=columns)
            return articles
        except psycopg2.Error as e:
            print(f"Error fetching articles: {e}")
            return pd.DataFrame()

    def rank_articles(self, user_query, num_articles=10):
        articles = self.get_articles_from_db()

        if articles.empty:
            print("No articles found in the database.")
            return pd.DataFrame()

        # Combine user query and article abstracts to create TF-IDF matrix
        combined_texts = [user_query] + articles['abstract'].fillna('').tolist()
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(combined_texts)

        # Calculate cosine similarity between user query and articles
        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        # Normalize cosine similarities
        cosine_similarities = cosine_similarities.reshape(-1, 1)
        cosine_scaler = MinMaxScaler()
        normalized_cosine_similarities = cosine_scaler.fit_transform(cosine_similarities).flatten()

        # Use the ML model to predict impact scores
        features = articles[[
            'publication_year',
            'delta_citations',
            'journal_h_index',
            'mean_citations_per_paper',
            'total_papers_published',
            'num_authors',
            'avg_author_h_index',
            'avg_author_total_papers',
            'avg_author_total_citations',
            'total_citations'
        ]].fillna(0)
        impact_scores = self.model.predict(features)

        # Normalize impact scores
        impact_scores = impact_scores.reshape(-1, 1)
        impact_scaler = MinMaxScaler()
        normalized_impact_scores = impact_scaler.fit_transform(impact_scores).flatten()

        # Combine the similarity and impact scores
        articles['cosine_sim'] = normalized_cosine_similarities
        articles['impact_score'] = normalized_impact_scores
        articles['combined_score'] = 0.7 * articles['cosine_sim'] + 0.3 * articles['impact_score']

        # Optional: Filter out articles with low cosine similarity
        min_similarity_threshold = 0.1  # Adjust as needed
        articles = articles[articles['cosine_sim'] >= min_similarity_threshold]

        if articles.empty:
            print("No articles match the query with sufficient similarity.")
            return pd.DataFrame()

        # Sort articles by combined score
        ranked_articles = articles.sort_values(by='combined_score', ascending=False)

        # Return the top N articles
        return ranked_articles.head(num_articles)