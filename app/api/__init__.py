from flask import Blueprint, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


def make_response(data=None, error=None, status=200):
    return jsonify({"data": data, "error": error}), status


@bp.route("/health", methods=["GET"])
def health():
    return make_response({"status": "ok"})
