from flask import Blueprint
bp = Blueprint("comparison", __name__, url_prefix="/comparison")
from . import routes
