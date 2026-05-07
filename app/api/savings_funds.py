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

  Fund:
    {
      "id": uuid,
      "title": str,
      "description": str | null,
      "current_amount": float,
      "target_amount": float | null,
      "monthly_contribution": float | null,
      "unallocated_amount": float,
      "is_completed": bool
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

from flask import current_app, g, request

from app.api import bp
from app.services import savings_funds_service

@bp.get("/savings/summary", strict_slashes=False)
def api_savings_summary():
    """
    Top-level summary data for savings page.

    Responses:
      200: {"data": {
            "current_balance": float,
            "total_in_funds": float,
            "funds_count": int,
            "total_unallocated_in_funds": float
          }, "error": null}
    """
    user_id = g.current_user.id
    result = savings_funds_service.get_savings_summary(user_id)
    return result.to_flask_response()


@bp.get("/funds", strict_slashes=False)
def api_funds_list():
    """
    List funds for carousel navigation.

    Responses:
      200: {"data": [Fund], "error": null}
    """
    user_id = g.current_user.id
    result = savings_funds_service.list_public_funds(user_id)
    return result.to_flask_response()


@bp.get("/funds/<uuid:fund_id>", strict_slashes=False)
def api_funds_get(fund_id: uuid.UUID):
    """
    Get one fund for carousel navigation.

    Responses:
      200: {"data": Fund, "error": null}
      404: see module errors
    """
    user_id = g.current_user.id
    result = savings_funds_service.get_public_fund(user_id, fund_id)
    return result.to_flask_response()


@bp.post("/funds", strict_slashes=False)
def api_funds_create():
    """
    Create fund.

    Request:
      {
        "title": str,
        "description": str | null,
        "target_amount": float | null,
        "monthly_contribution": float | null
      }

    Responses:
      201: {"data": Fund, "error": null}
      400: see module errors
    """
    user_id = g.current_user.id
    payload_in = request.get_json(silent=True) or {}

    result = savings_funds_service.create_public_fund(
        user_id,
        payload_in,
        max_savings_funds=current_app.config.get("MAX_SAVINGS_FUNDS", 10),
    )

    return result.to_flask_response()


@bp.patch("/funds/<uuid:fund_id>", strict_slashes=False)
@bp.put("/funds/<uuid:fund_id>", strict_slashes=False)
def api_funds_update(fund_id: uuid.UUID):
    """
    Update fund editable fields. Status is not updated here.

    Request:
      {
        "title": str,
        "description": str | null,
        "target_amount": float | null,
        "monthly_contribution": float | null
      }

    Responses:
      200: {"data": Fund, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = g.current_user.id
    payload_in = request.get_json(silent=True) or {}

    result = savings_funds_service.update_public_fund(
        user_id,
        fund_id,
        payload_in,
    )

    return result.to_flask_response()


@bp.delete("/funds/<uuid:fund_id>", strict_slashes=False)
def api_funds_delete(fund_id: uuid.UUID):
    """
    Delete fund.

    Responses:
      200: {"data": {"success": true}, "error": null}
      404: see module errors
    """
    user_id = g.current_user.id
    result = savings_funds_service.delete_public_fund(user_id, fund_id)
    return result.to_flask_response()


@bp.patch("/funds/<uuid:fund_id>/status", strict_slashes=False)
def api_funds_toggle_status(fund_id: uuid.UUID):
    """
    Toggle fund status.

    Request:
      {"is_completed": bool}

    Responses:
      200: {"data": {"id": uuid, "is_completed": bool}, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = g.current_user.id
    payload_in = request.get_json(silent=True) or {}

    result = savings_funds_service.update_fund_status(
        user_id,
        fund_id,
        payload_in,
    )

    return result.to_flask_response()

@bp.patch("/funds/<uuid:fund_id>/balance", strict_slashes=False)
def api_funds_adjust_balance(fund_id: uuid.UUID):
    """
    Adjust fund balance.

    Request:
      {"delta_amount": float}

    Examples:
      {"delta_amount": 100}   # add money
      {"delta_amount": -50}   # withdraw money

    Responses:
      200: {"data": Fund, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = g.current_user.id
    payload_in = request.get_json(silent=True) or {}

    if "delta_amount" not in payload_in:
        from app.services.errors import BadRequestError
        raise BadRequestError("Missing delta_amount")

    result = savings_funds_service.adjust_balance(
        user_id,
        fund_id,
        payload_in.get("delta_amount"),
    )

    return result.to_flask_response()