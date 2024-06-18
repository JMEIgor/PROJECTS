# app/routes/__init__.py

from flask import Blueprint

main_routes = Blueprint('main_routes', __name__)

from . import routes
