import uuid
from decimal import Decimal
from app.extensions import db
from app.models import Receipt, ReceiptItem
from app.models.category import Category

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

        item = ReceiptItem(
            receipt_id=receipt.id,
            user_id=receipt.user_id,
            category_id=data.get("category_id"),
            name=data.get("name"),
            quantity=Decimal(str(data.get("quantity", 1))),
            unit_price=Decimal(str(data.get("unit_price", 0))),
            total_price=Decimal(str(data.get("quantity", 1))) * Decimal(str(data.get("unit_price", 0))),
            extra_metadata=data.get("extra_metadata")
        )
        if item.category_id:
            category = db.session.get(Category, item.category_id)
            if not category:
                return {"error": "Category not found"}, 404
            category.count = (category.count or 0) + 1
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
        old_category_id = item.category_id  # likely uuid.UUID or None

        if "name" in data:
            item.name = data["name"]
        if "quantity" in data:
            item.quantity = Decimal(str(data["quantity"]))
        if "unit_price" in data:
            item.unit_price = Decimal(str(data["unit_price"]))
        if "category_id" in data:
            item.category_id = data["category_id"]
        if "extra_metadata" in data:
            item.extra_metadata = data["extra_metadata"]

        # always recalc total_price
        item.total_price = item.quantity * item.unit_price

        if "category_id" in data and old_category_id != item.category_id:
            # decrement old category
            if old_category_id:
                old_category = db.session.get(Category, old_category_id)
                if old_category and old_category.count > 0:
                    old_category.count -= 1

            # increment new category
            if item.category_id:
                new_category = db.session.get(Category, item.category_id)
                if new_category:
                    new_category.count = (new_category.count or 0) + 1

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

        if item.category_id:
            category = db.session.get(Category,item.category_id)
            if category and category.count > 0:
                    category.count -= 1

        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
