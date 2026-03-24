import uuid
from decimal import Decimal
from app.extensions import db
from app.models import Receipt, ReceiptItem
from app.validators.receipt_item_validators import validate_receipt_item_create_data, validate_receipt_item_update_data


def get_items_by_receipt(receipt_id: uuid.UUID):
    receipt = db.session.get(Receipt, receipt_id)
    if not receipt:
        return {"error": "Receipt not found"}, 404

    items = db.session.query(ReceiptItem).filter_by(receipt_id=receipt_id).all()
    result = []
    for item in items:
        result.append({
            "id": str(item.id),
            "receipt_id": str(item.receipt_id),
            "user_id": str(item.user_id),
            "category_id": str(item.category_id) if item.category_id else None,
            "name": item.name,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
            "total_price": float(item.total_price),
            "extra_metadata": item.extra_metadata
        })
    return result, 200


def create_item(receipt_id: uuid.UUID, data: dict):
    try:
        receipt = db.session.get(Receipt, receipt_id)
        if not receipt:
            return {"error": "Receipt not found"}, 404

        validated, err, status = validate_receipt_item_create_data(data)
        if err:
            return err, status

        item = ReceiptItem(
            receipt_id=receipt.id,
            user_id=receipt.user_id,
            category_id=validated["category_id"],
            name=validated["name"],
            quantity=validated["quantity"],
            unit_price=validated["unit_price"],
            total_price=validated["quantity"] * validated["unit_price"],
            extra_metadata=validated["extra_metadata"]
        )

        db.session.add(item)
        db.session.commit()
        return {"item_id": str(item.id), "message": "Item created successfully"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def update_item(receipt_id: uuid.UUID, item_id: uuid.UUID, data: dict):
    item = db.session.query(ReceiptItem).filter_by(id=item_id, receipt_id=receipt_id).first()
    if not item:
        return {"error": "Item not found"}, 404

    try:
        validated, err, status = validate_receipt_item_update_data(data)
        if err:
            return err, status

        if "name" in validated:
            item.name = validated["name"]
        if "quantity" in validated:
            item.quantity = validated["quantity"]
        if "unit_price" in validated:
            item.unit_price = validated["unit_price"]
        if "category_id" in validated:
            item.category_id = validated["category_id"]
        if "extra_metadata" in validated:
            item.extra_metadata = validated["extra_metadata"]

        item.total_price = item.quantity * item.unit_price

        db.session.commit()
        return {"item_id": str(item.id), "message": "Item updated successfully"}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def delete_item(receipt_id: uuid.UUID, item_id: uuid.UUID):
    item = db.session.query(ReceiptItem).filter_by(id=item_id, receipt_id=receipt_id).first()
    if not item:
        return {"error": "Item not found"}, 404

    try:
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


# TODO: Use this method to ensure that users only have access to their own receipt and prevent them from using other users' receipt.
def _get_receipt_for_user(receipt_id: uuid.UUID, user_id: uuid.UUID):
    receipt = db.session.get(Receipt, receipt_id)

    if not receipt:
        return None, {"error": "Receipt not found"}, 404

    if receipt.user_id != user_id:
        return None, {"error": "Forbidden"}, 403

    return receipt, None, None