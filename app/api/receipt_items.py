"""
Receipt Items API

Paths:
  - GET    /api/receipts/{receipt_id}/items
  - POST   /api/receipts/{receipt_id}/items
  - PUT    /api/receipts/{receipt_id}/items/{item_id}
  - DELETE /api/receipts/{receipt_id}/items/{item_id}

Swagger shows raw arrays/objects; actual API wraps payload in {"data": ...}.
"""

from flask import request
from app.api import bp, make_response
from app.services import receipt_items_service


@bp.get("/receipts/<uuid:receipt_id>/items", strict_slashes=False)
def api_receipt_items_get(receipt_id):
    """
    GET /api/receipts/{receipt_id}/items
    Summary: List items of a receipt

    Path:
      receipt_id: uuid

    Responses:
      200:
        data: [ { "id":"...","name":"...","quantity":n,"unit_price":n,"total_price":n }, ... ]
        error: null
      404:
        data: null
        error: {"code":"not_found","message":"Receipt not found"}
    """
    items, status = receipt_items_service.get_items_by_receipt(receipt_id)
    return make_response(items, None, status)


@bp.post("/receipts/<uuid:receipt_id>/items", strict_slashes=False)
def api_receipt_items_create(receipt_id):
    """
    POST /api/receipts/{receipt_id}/items
    Summary: Create item for a receipt

    Path:
      receipt_id: uuid

    Request (JSON example):
      {
        "category_id": "<uuid>",
        "name": "Banány",
        "quantity": 3,
        "unit_price": 0.9,
        "extra_metadata": { "discount": 0.1 }
      }

    Responses:
      201:
        data: {"item_id": "<uuid>", "message": "Item created successfully"}
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Missing JSON body"}
    """
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipt_items_service.create_item(receipt_id, payload)
    return make_response(response, None, status)


@bp.put("/receipts/<uuid:receipt_id>/items/<uuid:item_id>", strict_slashes=False)
def api_receipt_items_update(receipt_id, item_id):
    """
    PUT /api/receipts/{receipt_id}/items/{item_id}
    Summary: Update receipt item

    Path:
      receipt_id: uuid
      item_id: uuid

    Request (JSON example):
      { "name":"Maslo", "quantity":1, "unit_price":2.3, "extra_metadata":{"promo":true} }

    Responses:
      200:
        data: {"message":"Item updated successfully"}  # implementation defined
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Missing JSON body"}
      404:
        data: null
        error: {"code":"not_found","message":"Item not found"}
    """
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipt_items_service.update_item(receipt_id, item_id, payload)
    return make_response(response, None, status)


@bp.delete("/receipts/<uuid:receipt_id>/items/<uuid:item_id>", strict_slashes=False)
def api_receipt_items_delete(receipt_id, item_id):
    """
    DELETE /api/receipts/{receipt_id}/items/{item_id}
    Summary: Delete receipt item

    Path:
      receipt_id: uuid
      item_id: uuid

    Responses:
      200:
        data: {"message":"Item deleted successfully"}  # implementation defined
        error: null
      404:
        data: null
        error: {"code":"not_found","message":"Item not found"}
    """
    response, status = receipt_items_service.delete_item(receipt_id, item_id)
    return make_response(response, None, status)
