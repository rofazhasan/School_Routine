from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()
# Initialize the database
db = SQLAlchemy()

# Function to initialize the database with the Flask app
def init_app(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    db.init_app(app)