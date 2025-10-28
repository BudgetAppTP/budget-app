from flask import Blueprint

bp = Blueprint("receipt_items", __name__, url_prefix="/api/receipts")

from . import routes
