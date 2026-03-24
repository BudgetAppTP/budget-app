"""
Users API

Paths:
  - GET  /api/users/     List users
  - POST /api/users/     Create user

Notes:
- Сервис возвращает структуру, которую мы оборачиваем в {"data": ...}.
- Для согласованности со Swagger включён strict_slashes=False.
"""

from flask import request
from app.api import bp
from app.services.errors import BadRequestError
from app.services import users_service


@bp.get("/users", strict_slashes=False)
def api_users_list():
    """
    GET /api/users/
    Summary: List users

    Responses:
      200:
        data: {
          "users": [
            {"id":"<uuid>","email":"user@example.com","...":"..."},
            ...
          ]
        }
        error: null
    """
    result = users_service.get_all_users()
    return result.to_flask_response()


@bp.post("/users", strict_slashes=False)
def api_users_create():
    """
    POST /api/users/
    Summary: Create user

    Request (JSON):
      {"email":"user@example.com","password":"***", "...":"..."}

    Responses:
      201:
        data: {"id":"<uuid>", "email":"user@example.com", "...":"..."}
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Missing JSON body"}
    """
    payload = request.get_json() or {}
    if not payload:
        raise BadRequestError("Missing JSON body")
    result = users_service.create_user(payload)
    return result.to_flask_response()
