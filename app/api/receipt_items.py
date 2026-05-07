"""
Receipt Items API

Paths:
  - GET    /api/receipts/{receipt_id}/items
  - POST   /api/receipts/{receipt_id}/items
  - PUT    /api/receipts/{receipt_id}/items/{item_id}
  - DELETE /api/receipts/{receipt_id}/items/{item_id}

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  ReceiptItem:
    {
      "id": uuid,
      "receipt_id": uuid,
      "user_id": uuid,
      "category_id": "uuid | null",
      "name": str,
      "quantity": float,
      "unit_price": float,
      "total_price": float,
      "extra_metadata": "object | null"
    }

  ReceiptItemList:
    [ReceiptItem]

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
"""

import uuid

from flask import g

from app.api import bp
from app.api.request_parsing import parse_json_object_body
from app.services import receipt_items_service


@bp.get("/receipts/<uuid:receipt_id>/items", strict_slashes=False)
def api_receipt_items_get(receipt_id: uuid.UUID):
    """
    List receipt items for one receipt owned by the authenticated user.

    Path:
      receipt_id: uuid

    Responses:
      200: {"data": ReceiptItemList, "error": null}
      404: see module errors
    """
    result = receipt_items_service.get_items_by_receipt(receipt_id, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.post("/receipts/<uuid:receipt_id>/items", strict_slashes=False)
def api_receipt_items_create(receipt_id: uuid.UUID):
    """
    Create one receipt item on a receipt owned by the authenticated user.

    Path:
      receipt_id: uuid

    Request:
      {
        "category_id": "uuid | null | omitted",
        "name": str,
        "quantity": float,
        "unit_price": float,
        "extra_metadata": "object | null | omitted"
      }

    Responses:
      201: {"data": {"item_id": uuid, "message": str}, "error": null}
      400: see module errors
      404: see module errors
    """
    payload = parse_json_object_body(allow_empty=False)
    result = receipt_items_service.create_item(receipt_id, user_id=g.current_user.id, data=payload)
    return result.to_flask_response()


@bp.put("/receipts/<uuid:receipt_id>/items/<uuid:item_id>", strict_slashes=False)
def api_receipt_items_update(receipt_id: uuid.UUID, item_id: uuid.UUID):
    """
    Update one receipt item owned by the authenticated user.

    Path:
      receipt_id: uuid
      item_id: uuid

    Request:
      {
        "category_id": "uuid | null | omitted",
        "name": "str | omitted",
        "quantity": "float | omitted",
        "unit_price": "float | omitted",
        "extra_metadata": "object | null | omitted"
      }

    Responses:
      200: {"data": {"item_id": uuid, "message": str}, "error": null}
      400: see module errors
      404: see module errors
    """
    payload = parse_json_object_body(allow_empty=False)
    result = receipt_items_service.update_item(
        receipt_id,
        item_id,
        user_id=g.current_user.id,
        data=payload,
    )
    return result.to_flask_response()


@bp.delete("/receipts/<uuid:receipt_id>/items/<uuid:item_id>", strict_slashes=False)
def api_receipt_items_delete(receipt_id: uuid.UUID, item_id: uuid.UUID):
    """
    Delete one receipt item owned by the authenticated user.

    Path:
      receipt_id: uuid
      item_id: uuid

    Responses:
      200: {"data": {"message": str}, "error": null}
      404: see module errors
    """
    result = receipt_items_service.delete_item(receipt_id, item_id, user_id=g.current_user.id)
    return result.to_flask_response()
