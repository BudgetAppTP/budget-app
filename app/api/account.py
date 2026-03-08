"""
Account API

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  Account:
    {
      "id": uuid,
      "name": str,
      "balance": float,
      "currency": str (ISO 4217),
      "account_type": str
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
"""

from flask import request

from app.api import bp
from app.api.auth_context import get_mock_user_id
from app.services import accounts_service

@bp.get("/account", strict_slashes=False)
def api_account_get():
    """
    Get the current user's main account.

    Responses:
      200: {"data": Account, "error": null}
      404: see module errors
    """
    user_id = get_mock_user_id()
    result = accounts_service.get_main_account(user_id)
    return result.to_flask_response()


@bp.patch("/account", strict_slashes=False)
def api_account_patch():
    """
    Update mutable fields of the current user's main account.

    Request:
      {"name"?: str, "currency"?: str (ISO 4217)}

    Responses:
      200: {"data": Account, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = accounts_service.update_main_account(user_id, payload_in)
    return result.to_flask_response()
