from flask import Blueprint
bp = Blueprint("transactions", __name__, url_prefix="/transactions")
from . import routes
