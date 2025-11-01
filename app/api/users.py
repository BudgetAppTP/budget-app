from flask import request
from app.api import bp, make_response
from app.services import users_service

@bp.get("/users")
def api_users_list():
    users = users_service.get_all_users()
    return make_response(users, None, 200)

@bp.post("/users")
def api_users_create():
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = users_service.create_user(payload)
    return make_response(response, None, status)
