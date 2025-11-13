"""
Receipts API

Paths:
  - GET    /api/receipts/                 List receipts
  - POST   /api/receipts/                 Create receipt
  - GET    /api/receipts/{receipt_id}     Get receipt by id
  - PUT    /api/receipts/{receipt_id}     Update receipt
  - DELETE /api/receipts/{receipt_id}     Delete receipt

Notes:
- Swagger может показывать «сырой» JSON (без конверта). Фактический ответ — в конверте:
  { "data": <payload>, "error": null }.
"""

from flask import request
from app.api import bp, make_response
from app.services import receipts_service


@bp.get("/receipts", strict_slashes=False)
def api_receipts_list():
    """
    GET /api/receipts/
    Summary: List receipts

    Responses:
      200:
        data: {
          "receipts": [
            {"id":"<uuid>","date":"YYYY-MM-DD","seller":"...", "total": number, ...},
            ...
          ]
        }
        error: null
    """
    receipts = receipts_service.get_all_receipts()
    return make_response(receipts, None, 200)


@bp.post("/receipts", strict_slashes=False)
def api_receipts_create():
    """
    POST /api/receipts/
    Summary: Create receipt

    Request (JSON):
      {
        "date":"YYYY-MM-DD",
        "seller":"Tesco, a.s.",
        "total": 23.45,
        "...": "..."
      }

    Responses:
      201:
        data: {"id":"<uuid>", "...": "..."}
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Missing JSON body"}
    """
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipts_service.create_receipt(payload)
    return make_response(response, None, status)


@bp.get("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_get(receipt_id):
    """
    GET /api/receipts/{receipt_id}
    Summary: Get receipt by id

    Path:
      receipt_id: uuid

    Responses:
      200:
        data: {"id":"<uuid>","date":"YYYY-MM-DD","seller":"...", "total": number, ...}
        error: null
      404:
        data: null
        error: {"code":"not_found","message":"Receipt not found"}
    """
    receipt, status = receipts_service.get_receipt_by_id(receipt_id)
    return make_response(receipt, None, status)


@bp.put("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_update(receipt_id):
    """
    PUT /api/receipts/{receipt_id}
    Summary: Update receipt

    Request (JSON):
      {"date":"YYYY-MM-DD","seller":"...","total": number, ...}

    Responses:
      200:
        data: {"message":"Receipt updated successfully", "...": "..."}  # impl-defined
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Missing JSON body"}
      404:
        data: null
        error: {"code":"not_found","message":"Receipt not found"}
    """
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipts_service.update_receipt(receipt_id, payload)
    return make_response(response, None, status)


@bp.delete("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_delete(receipt_id):
    """
    DELETE /api/receipts/{receipt_id}
    Summary: Delete receipt

    Responses:
      200:
        data: {"message":"Receipt deleted successfully"}  # impl-defined
        error: null
      404:
        data: null
        error: {"code":"not_found","message":"Receipt not found"}
    """
    response, status = receipts_service.delete_receipt(receipt_id)
    return make_response(response, None, status)
