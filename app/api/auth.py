"""
Auth API

Paths:
  - POST /api/auth/login
  - POST /api/auth/register
  - POST /api/auth/logout

Notes:
- Payload minimal: email + password
- On success returns {"ok": true} or {"created": true, "id": "..."} in data field
"""

import uuid
from flask import request, current_app
from app.api import bp, make_response
from app.core.domain import User


def _services():
    return current_app.extensions["services"]


@bp.post("/auth/login", strict_slashes=False)
def api_login():
    """
    POST /api/auth/login
    Summary: User login

    Request:
      {"email":"user@example.com","password":"***"}

    Responses:
      200: {"data":{"ok":true}, "error":null}
      401: {"data":null,"error":{"code":"auth_failed","message":"Invalid credentials"}}
    """
    p = request.get_json(silent=True) or {}
    email = p.get("email", "").strip()
    password = p.get("password", "")
    ok = _services().auth.login(email, password, _services().users)
    if not ok:
        return make_response(None, {"code": "auth_failed", "message": "Invalid credentials"}, 401)
    return make_response({"ok": True})


@bp.post("/auth/register", strict_slashes=False)
def api_register():
    """
    POST /api/auth/register
    Summary: User registration

    Request:
      {"email":"user@example.com","password":"***"}

    Responses:
      201: {"data":{"created":true,"id":"<uuid>"},"error":null}
      400: {"data":null,"error":{"code":"bad_request","message":"email and password required"}}
      409: {"data":null,"error":{"code":"exists","message":"User already exists"}}
    """
    p = request.get_json(silent=True) or {}
    email = p.get("email", "").strip()
    password = p.get("password", "")
    if not email or not password:
        return make_response(None, {"code": "bad_request", "message": "email and password required"}, 400)
    if _services().users.get_by_email(email):
        return make_response(None, {"code": "exists", "message": "User already exists"}, 409)
    uid = str(uuid.uuid4())
    pwd_hash = _services().auth.hash_password(password)
    _services().users.add(User(uid, email, pwd_hash))
    return make_response({"created": True, "id": uid}, None, 201)


@bp.post("/auth/logout", strict_slashes=False)
def api_logout():
    """
    POST /api/auth/logout
    Summary: User logout

    Responses:
      200:
        {"data":{"ok":true},"error":null}
    """
    _services().auth.logout()
    return make_response({"ok": True})
