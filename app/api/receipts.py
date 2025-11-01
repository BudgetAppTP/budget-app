from flask import request
from app.api import bp, make_response
from app.services import receipts_service

@bp.get("/receipts")
def api_receipts_list():
    receipts = receipts_service.get_all_receipts()
    return make_response(receipts, None, 200)

@bp.post("/receipts")
def api_receipts_create():
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipts_service.create_receipt(payload)
    return make_response(response, None, status)

@bp.get("/receipts/<uuid:receipt_id>")
def api_receipts_get(receipt_id):
    receipt, status = receipts_service.get_receipt_by_id(receipt_id)
    return make_response(receipt, None, status)

@bp.put("/receipts/<uuid:receipt_id>")
def api_receipts_update(receipt_id):
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipts_service.update_receipt(receipt_id, payload)
    return make_response(response, None, status)

@bp.delete("/receipts/<uuid:receipt_id>")
def api_receipts_delete(receipt_id):
    response, status = receipts_service.delete_receipt(receipt_id)
    return make_response(response, None, status)
