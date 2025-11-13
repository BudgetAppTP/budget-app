from flask import Blueprint

bp = Blueprint("users", __name__, url_prefix="/api/users")

from . import routes
