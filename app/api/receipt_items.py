from flask import request
from app.api import bp, make_response
from app.services import receipt_items_service

@bp.get("/receipts/<uuid:receipt_id>/items")
def api_receipt_items_get(receipt_id):
    items, status = receipt_items_service.get_items_by_receipt(receipt_id)
    return make_response(items, None, status)

@bp.post("/receipts/<uuid:receipt_id>/items")
def api_receipt_items_create(receipt_id):
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipt_items_service.create_item(receipt_id, payload)
    return make_response(response, None, status)

@bp.put("/receipts/<uuid:receipt_id>/items/<uuid:item_id>")
def api_receipt_items_update(receipt_id, item_id):
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipt_items_service.update_item(receipt_id, item_id, payload)
    return make_response(response, None, status)

@bp.delete("/receipts/<uuid:receipt_id>/items/<uuid:item_id>")
def api_receipt_items_delete(receipt_id, item_id):
    response, status = receipt_items_service.delete_item(receipt_id, item_id)
    return make_response(response, None, status)
