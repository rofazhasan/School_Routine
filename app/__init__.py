from flask import Flask
from app.database import db, init_app
from app.routes import app

def create_app():
    routes = Flask (__name__)
    init_app(routes)  # Initialize the database with the app

    routes.register_blueprint(app)  # Register the blueprint

    return routes
