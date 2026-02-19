from flask import Blueprint
bp = Blueprint("needs", __name__, url_prefix="/needs")
from . import routes
