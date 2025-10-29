from flask import Blueprint
bp = Blueprint("eKasa", __name__, url_prefix="/eKasa")
from . import routes
