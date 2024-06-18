# app/__init__.py

from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():
        # Importar as rotas
        from .routes import main_routes
        app.register_blueprint(main_routes)

    return app
