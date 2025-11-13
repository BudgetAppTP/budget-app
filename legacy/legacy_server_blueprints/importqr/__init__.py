from flask import Blueprint
bp = Blueprint("importqr", __name__, url_prefix="/import-qr")
from . import routes
