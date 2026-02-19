"""
API Blueprint

Contract:
- Base prefix: /api
- Unified envelope: {"data": <payload>|null, "error": {"code": str, "message": str}|null}
- Errors are always JSON via global handlers.

Notes for Swagger:
- Some swagger examples show raw JSON. Actual responses are wrapped in the envelope above.
"""

from flask import Blueprint, jsonify

bp = Blueprint("api", __name__, url_prefix="/api")


def make_response(data=None, error=None, status=200):
    """
    Make unified API response.

    Returns:
      JSON:
        {
          "data": any or null,
          "error": {"code": str, "message": str} or null
        }
    """
    return jsonify({"data": data, "error": error}), status


@bp.route("/health", methods=["GET"], strict_slashes=False)
def health():
    """
    GET /api/health
    Summary: Liveness probe

    Responses:
      200:
        data:
          {
            "status": "ok"
          }
        error: null
    """
    return make_response({"status": "ok"})
