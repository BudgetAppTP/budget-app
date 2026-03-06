import uuid

from flask import current_app, request

from app.api import bp
from app.api.auth_context import get_mock_user_id
from app.services import savings_funds_service

@bp.get("/savings-funds", strict_slashes=False)
def api_savings_funds_list():
    user_id = get_mock_user_id()
    result = savings_funds_service.list_funds(user_id)
    return result.to_flask_response()


@bp.post("/savings-funds", strict_slashes=False)
def api_savings_funds_create():
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = savings_funds_service.create_fund(
        user_id,
        payload_in,
        max_savings_funds=current_app.config.get("MAX_SAVINGS_FUNDS", 10),
    )
    return result.to_flask_response()


@bp.get("/savings-funds/<uuid:fund_id>", strict_slashes=False)
def api_savings_funds_get(fund_id: uuid.UUID):
    user_id = get_mock_user_id()
    result = savings_funds_service.get_fund(user_id, fund_id)
    return result.to_flask_response()


@bp.patch("/savings-funds/<uuid:fund_id>", strict_slashes=False)
def api_savings_funds_update(fund_id: uuid.UUID):
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = savings_funds_service.update_fund(user_id, fund_id, payload_in)
    return result.to_flask_response()


@bp.delete("/savings-funds/<uuid:fund_id>", strict_slashes=False)
def api_savings_funds_delete(fund_id: uuid.UUID):
    user_id = get_mock_user_id()
    result = savings_funds_service.delete_fund(user_id, fund_id)
    return result.to_flask_response()


@bp.post("/savings-funds/<uuid:fund_id>/balance-adjustments", strict_slashes=False)
def api_savings_funds_balance_adjust(fund_id: uuid.UUID):
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = savings_funds_service.adjust_balance(
        user_id,
        fund_id,
        payload_in.get("delta_amount"),
    )
    return result.to_flask_response()
