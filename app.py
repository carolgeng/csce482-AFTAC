from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure the app to use Heroku's PostgreSQL database URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')  # Heroku adds this automatically
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import your models here
from models import Paper, Author, Journal, Citation

@app.route('/')
def index():
    return jsonify({"message": "Hello, world!"})

if __name__ == '__main__':
    app.run(debug=True)

