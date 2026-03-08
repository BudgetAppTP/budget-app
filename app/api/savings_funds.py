"""
Savings Funds API

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  SavingsFund:
    {
      "id": uuid,
      "name": str,
      "balance": float,
      "currency": str (ISO 4217),
      "target_amount": float | null,
      "monthly_contribution": float | null,
      "unused_amount": float
    }

  SavingsFundList:
    {"items": [SavingsFund], "count": int}

  FundDeleted:
    {"id": uuid}

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
"""

import uuid

from flask import current_app, request

from app.api import bp
from app.api.auth_context import get_mock_user_id
from app.services import savings_funds_service

@bp.get("/savings-funds", strict_slashes=False)
def api_savings_funds_list():
    """
    List savings funds available to current user.

    Responses:
      200: {"data": SavingsFundList, "error": null}
    """
    user_id = get_mock_user_id()
    result = savings_funds_service.list_funds(user_id)
    return result.to_flask_response()


@bp.post("/savings-funds", strict_slashes=False)
def api_savings_funds_create():
    """
    Create a new savings fund for current user.

    Request:
      {"name": str, "currency": str (ISO 4217), "target_amount"?: float, "monthly_contribution"?: float}

    Responses:
      201: {"data": SavingsFund, "error": null}
      400: see module errors
    """
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
    """
    Get one savings fund by id.

    Responses:
      200: {"data": SavingsFund, "error": null}
      404: see module errors
    """
    user_id = get_mock_user_id()
    result = savings_funds_service.get_fund(user_id, fund_id)
    return result.to_flask_response()


@bp.patch("/savings-funds/<uuid:fund_id>", strict_slashes=False)
def api_savings_funds_update(fund_id: uuid.UUID):
    """
    Update mutable savings fund fields.

    Request:
      {"name"?: str, "currency"?: str (ISO 4217), "target_amount"?: float | null, "monthly_contribution"?: float | null}

    Responses:
      200: {"data": SavingsFund, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = savings_funds_service.update_fund(user_id, fund_id, payload_in)
    return result.to_flask_response()


@bp.delete("/savings-funds/<uuid:fund_id>", strict_slashes=False)
def api_savings_funds_delete(fund_id: uuid.UUID):
    """
    Delete a savings fund by id.

    Responses:
      200: {"data": FundDeleted, "error": null}
      404: see module errors
    """
    user_id = get_mock_user_id()
    result = savings_funds_service.delete_fund(user_id, fund_id)
    return result.to_flask_response()


@bp.post("/savings-funds/<uuid:fund_id>/balance-adjustments", strict_slashes=False)
def api_savings_funds_balance_adjust(fund_id: uuid.UUID):
    """
    Apply balance delta to a savings fund.

    Request:
      {"delta_amount": float}

    Responses:
      200: {"data": SavingsFund, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = savings_funds_service.adjust_balance(
        user_id,
        fund_id,
        payload_in.get("delta_amount"),
    )
    return result.to_flask_response()
