from flask import request, jsonify
from . import bp
from app.services import receipts_service


@bp.route("/", methods=["GET"])
def get_receipts():
    receipts = receipts_service.get_all_receipts()
    return jsonify(receipts), 200


@bp.route("/", methods=["POST"])
def create_receipt():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    response, status = receipts_service.create_receipt(data)
    return jsonify(response), status


@bp.route("/<uuid:receipt_id>", methods=["GET"])
def get_receipt(receipt_id):
    receipt, status = receipts_service.get_receipt_by_id(receipt_id)
    return jsonify(receipt), status


@bp.route("/<uuid:receipt_id>", methods=["PUT"])
def update_receipt(receipt_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    response, status = receipts_service.update_receipt(receipt_id, data)
    return jsonify(response), status


@bp.route("/<uuid:receipt_id>", methods=["DELETE"])
def delete_receipt(receipt_id):
    response, status = receipts_service.delete_receipt(receipt_id)
    return jsonify(response), status