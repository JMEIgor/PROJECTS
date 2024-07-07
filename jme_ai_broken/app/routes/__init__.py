from flask import Blueprint

# Define um blueprint chamado 'main_routes'
main_routes = Blueprint('main_routes', __name__)

from . import routes
