from flask import Flask
from config import Config

def create_app():
    # Cria a instância da aplicação Flask
    app = Flask(__name__)
    
    # Carrega a configuração da aplicação
    app.config.from_object(Config)

    # Registra os blueprints dentro do contexto da aplicação
    with app.app_context():
        from .routes import main_routes
        app.register_blueprint(main_routes)

    return app
