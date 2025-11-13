from flask import request, jsonify
from . import bp
from app.services import receipt_items_service


@bp.route("/<uuid:receipt_id>/items", methods=["GET"])
def get_items(receipt_id):
    """Get all items for a given receipt."""
    items, status = receipt_items_service.get_items_by_receipt(receipt_id)
    return jsonify(items), status


@bp.route("/<uuid:receipt_id>/items", methods=["POST"])
def create_item(receipt_id):
    """Create a new item for a given receipt."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    response, status = receipt_items_service.create_item(receipt_id, data)
    return jsonify(response), status


@bp.route("/<uuid:receipt_id>/items/<uuid:item_id>", methods=["PUT"])
def update_item(receipt_id, item_id):
    """Update an existing item on a receipt."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    response, status = receipt_items_service.update_item(receipt_id, item_id, data)
    return jsonify(response), status


@bp.route("/<uuid:receipt_id>/items/<uuid:item_id>", methods=["DELETE"])
def delete_item(receipt_id, item_id):
    """Delete a receipt item."""
    response, status = receipt_items_service.delete_item(receipt_id, item_id)
    return jsonify(response), status
