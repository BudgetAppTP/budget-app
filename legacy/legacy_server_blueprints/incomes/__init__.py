from flask import Blueprint

bp = Blueprint("incomes", __name__, url_prefix="/api/incomes")

from . import routes
