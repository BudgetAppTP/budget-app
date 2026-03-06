from flask import request

from app.api import bp
from app.api.auth_context import get_mock_user_id
from app.services import accounts_service

@bp.get("/account", strict_slashes=False)
def api_account_get():
    user_id = get_mock_user_id()
    result = accounts_service.get_main_account(user_id)
    return result.to_flask_response()


@bp.patch("/account", strict_slashes=False)
def api_account_patch():
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = accounts_service.update_main_account(user_id, payload_in)
    return result.to_flask_response()
