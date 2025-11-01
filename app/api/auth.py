import uuid
from flask import request, current_app
from app.api import bp, make_response
from app.core.domain import User

def _services():
    return current_app.extensions["services"]

@bp.post("/auth/login")
def api_login():
    p = request.get_json(silent=True) or {}
    email = p.get("email", "").strip()
    password = p.get("password", "")
    ok = _services().auth.login(email, password, _services().users)
    if not ok:
        return make_response(None, {"code": "auth_failed", "message": "Invalid credentials"}, 401)
    return make_response({"ok": True})

@bp.post("/auth/register")
def api_register():
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

@bp.post("/auth/logout")
def api_logout():
    _services().auth.logout()
    return make_response({"ok": True})
