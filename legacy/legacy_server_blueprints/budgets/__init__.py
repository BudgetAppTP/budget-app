from flask import Blueprint
bp = Blueprint("budgets", __name__, url_prefix="/budgets")
from . import routes
