import os
import psycopg2
import pandas as pd
import pickle
import re
from datetime import datetime
from sklearn.neural_network import MLPClassifier  # Using classifier instead of regressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database.DatabaseManager import DatabaseManager
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.inspection import permutation_importance


class RankModel:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.database_url = os.getenv('DATABASE_URL')
        self.connection = psycopg2.connect(self.database_url)
        self.db_manager = DatabaseManager()
        self.scaler = None
        self.model = self.load_model()
    
    def load_model(self):
        model_file = 'ml_model.pkl'
        scaler_file = 'scaler.pkl'
        if os.path.exists(model_file) and os.path.exists(scaler_file):
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            with open(scaler_file, 'rb') as f:
                self.scaler = pickle.load(f)
            print("Loaded existing ML model.")
        else:
            print("Training new ML model...")
            model = self.train_ml_model()
        return model
    
    def train_ml_model(self):
        # Fetch articles data from the database
        articles = self.get_articles_from_db()

        # Parse the list of influential articles
        influential_titles = self.get_influential_titles('top100MLpapers.txt')

        # Label articles
        articles['is_influential'] = articles['title'].apply(
            lambda x: 1 if x.lower() in influential_titles else 0
        )

        # Handle class imbalance
        from sklearn.utils import resample

        # Separate majority and minority classes
        df_majority = articles[articles.is_influential == 0]
        df_minority = articles[articles.is_influential == 1]

        if df_minority.empty:
            print("No influential articles found in the dataset.")
            return None

        # Upsample minority class
        df_minority_upsampled = resample(
            df_minority,
            replace=True,     # sample with replacement
            n_samples=len(df_majority),    # to match majority class
            random_state=42   # reproducible results
        )

        # Combine majority class with upsampled minority class
        articles_balanced = pd.concat([df_majority, df_minority_upsampled])

        # Shuffle the dataset
        articles_balanced = articles_balanced.sample(
            frac=1, random_state=42
        ).reset_index(drop=True)

        # Feature Engineering
        current_year = datetime.now().year
        articles_balanced['publication_age'] = current_year - articles_balanced['publication_year']

        # Select relevant features
        features = articles_balanced[[
            'publication_age',
            'delta_citations',
            'journal_h_index',
            'mean_citations_per_paper',
            'total_papers_published',
            'num_authors',
            'avg_author_h_index',
            'avg_author_total_papers',
            'avg_author_total_citations'
        ]]
        target = articles_balanced['is_influential']

        # Handle missing values
        features = features.fillna(features.mean())

        # Feature scaling
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        self.scaler = scaler

        # ------------------ Part 2a: Check for Data Leakage ------------------

        # Calculate correlation between features and target
        correlation = features.apply(lambda x: x.corr(target))
        print("Feature-Target Correlation:")
        print(correlation.sort_values(ascending=False))

        # Identify features with high correlation (absolute value > 0.8)
        high_corr_features = correlation[correlation.abs() > 0.8].index.tolist()
        print(f"Highly correlated features: {high_corr_features}")

        # Remove highly correlated features to prevent data leakage
        if high_corr_features:
            print("Removing highly correlated features to prevent data leakage...")
            features = features.drop(columns=high_corr_features)
            # Re-scale features after dropping columns
            features_scaled = scaler.fit_transform(features)
            self.scaler = scaler

        # ------------------ Part 2b: Validate Model Generalization ------------------

        # Initialize the model
        model = MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation='relu',
            solver='adam',
            max_iter=500,
            random_state=42
        )

        # Perform cross-validation
        cv_scores = cross_val_score(
            model, features_scaled, target, cv=5, scoring='roc_auc'
        )
        print(f"Cross-Validated ROC AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        # Proceed to split data
        X_train, X_test, y_train, y_test = train_test_split(
            features_scaled, target, test_size=0.2, random_state=42, stratify=target
        )

        # Train the model
        model.fit(X_train, y_train)

        # Evaluate the model
        y_pred = model.predict(X_test)
        print("Classification Report:")
        print(classification_report(y_test, y_pred))
        print('ROC AUC Score:', roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))

        # Permutation Feature Importance
        result = permutation_importance(
            model, X_test, y_test, n_repeats=10, random_state=42
        )
        importance_df = pd.DataFrame({
            'Feature': features.columns,
            'Importance': result.importances_mean
        })
        print("Permutation Feature Importances:")
        print(importance_df.sort_values(by='Importance', ascending=False))

        # Save the model and scaler
        with open('scaler.pkl', 'wb') as f:
            pickle.dump(scaler, f)
        with open('ml_model.pkl', 'wb') as f:
            pickle.dump(model, f)

        return model

    def get_influential_titles(self, filepath):
        influential_titles = []
        try:
            with open(filepath, 'r') as file:
                content = file.read()
                # Extract titles using regex
                titles = re.findall(r'title=\{(.+?)\},', content, re.DOTALL)
                influential_titles = [title.strip().lower() for title in titles]
            return set(influential_titles)
        except FileNotFoundError:
            print(f"File {filepath} not found.")
            return set()

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
                j.journal_name,  
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
            GROUP BY
                p.id,
                j.journal_name,  
                j.journal_h_index,
                j.mean_citations_per_paper,
                j.total_papers_published
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

        # Prepare features for prediction
        current_year = datetime.now().year
        articles['publication_age'] = current_year - articles['publication_year']

        features = articles[[
            'publication_age',
            'delta_citations',
            'journal_h_index',
            'mean_citations_per_paper',
            'total_papers_published',
            'num_authors',
            'avg_author_h_index',
            'avg_author_total_papers',
            'avg_author_total_citations'
        ]]

        # Ensure consistency with training features
        if hasattr(self.scaler, 'feature_names_in_'):
            training_features = list(self.scaler.feature_names_in_)
            features = features[training_features]

        # Handle missing values
        features = features.fillna(features.mean())

        # Feature scaling
        if self.scaler is None:
            print("Scaler not found, cannot proceed.")
            return pd.DataFrame()
        features_scaled = self.scaler.transform(features)

        # Predict impact scores using the trained classifier
        impact_scores = self.model.predict_proba(features_scaled)[:, 1]

        # Normalize impact scores
        impact_scores = impact_scores.reshape(-1, 1)
        impact_scaler = MinMaxScaler()
        normalized_impact_scores = impact_scaler.fit_transform(impact_scores).flatten()

        print(f"Impact scores: {impact_scores[:10]}")


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
