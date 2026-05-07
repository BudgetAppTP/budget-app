"""
Users API

Paths:
  - GET  /api/users
  - POST /api/users

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
  403: {"data": null, "error": {"code": "forbidden", "message": str}}
  409: {"data": null, "error": {"code": "conflict", "message": str}}
"""

from flask import g

from app.api import bp
from app.api.request_parsing import parse_json_object_body
from app.services import users_service


@bp.get("/users", strict_slashes=False)
def api_users_list():
    """
    List all users.

    Responses:
      200: {"data": [User], "error": null}
      403: {"data": null, "error": {"code": "forbidden", "message": str}}
    """
    user_id = g.current_user.id
    result = users_service.get_all_users(user_id)
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
      403: see module errors
      409: see module errors
    """
    payload = parse_json_object_body(allow_empty=False)
    user_id = g.current_user.id
    result = users_service.create_user(user_id, payload)
    return result.to_flask_response()
