"""
Users API

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  User:
    {
      "id": uuid,
      "username": str,
      "email": str,
      "created_at": str | null
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  409: {"data": null, "error": {"code": "conflict", "message": str}}
"""

from flask import request

from app.api import bp
from app.services.errors import BadRequestError
from app.services import users_service


@bp.get("/users", strict_slashes=False)
def api_users_list():
    """
    List all users.

    Responses:
      200: {"data": [User], "error": null}
    """
    result = users_service.get_all_users()
    return result.to_flask_response()


@bp.post("/users", strict_slashes=False)
def api_users_create():
    """
    Create a user.

    Request:
      {
        "username": str,
        "email": str,
        "password": str,
        "currency"?: str (ISO 4217)
      }

    Responses:
      201: {"data": {"id": uuid, "message": str}, "error": null}
      400: see module errors
      409: see module errors
    """
    payload = request.get_json() or {}
    if not payload:
        raise BadRequestError("Missing JSON body")
    result = users_service.create_user(payload)
    return result.to_flask_response()
