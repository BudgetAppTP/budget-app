"""
Allocations API

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  Allocation:
    {
      "id": uuid,
      "allocation_date": "YYYY-MM-DD",
      "amount": float,
      "source_account_id": uuid,
      "target_account_id": uuid
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
"""

import uuid

from flask import request

from app.api import bp
from app.api.auth_context import get_mock_user_id
from app.services import allocations_service


@bp.get("/savings-funds/<uuid:fund_id>/allocations", strict_slashes=False)
def api_allocations_list(fund_id: uuid.UUID):
    """
    List allocations made to the selected savings fund.

    Responses:
      200: {"data": {"items": [Allocation], "count": int}, "error": null}
      404: see module errors
    """
    user_id = get_mock_user_id()
    result = allocations_service.list_allocations(user_id, fund_id)
    return result.to_flask_response()


@bp.post("/savings-funds/<uuid:fund_id>/allocations", strict_slashes=False)
def api_allocations_create(fund_id: uuid.UUID):
    """
    Create allocation from current user's main account to selected savings fund.

    Request:
      {"amount": float}

    Responses:
      201: {"data": Allocation, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = get_mock_user_id()
    payload_in = request.get_json(silent=True) or {}
    result = allocations_service.create_allocation(user_id, fund_id, payload_in)
    return result.to_flask_response()


@bp.delete("/savings-funds/<uuid:fund_id>/allocations/<uuid:allocation_id>", strict_slashes=False)
def api_allocations_undo(fund_id: uuid.UUID, allocation_id: uuid.UUID):
    """
    Undo allocation by deleting allocation record and reversing balances.

    Responses:
      200: {"data": {"id": uuid}, "error": null}
      400: see module errors
      404: see module errors
    """
    user_id = get_mock_user_id()
    result = allocations_service.undo_allocation(user_id, fund_id, allocation_id)
    return result.to_flask_response()
