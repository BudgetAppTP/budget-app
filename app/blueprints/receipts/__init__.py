from flask import Blueprint

bp = Blueprint("receipts", __name__, url_prefix="/api/receipts")

from . import routes
