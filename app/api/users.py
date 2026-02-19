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
from app.api import bp, make_response
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
    users = users_service.get_all_users()
    return make_response(users, None, 200)


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
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = users_service.create_user(payload)
    return make_response(response, None, status)
