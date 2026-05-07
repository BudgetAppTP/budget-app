import uuid

from app.extensions import db
from app.models.category import Category
from app.models import Receipt, ReceiptItem
from app.services.errors import NotFoundError
from app.services.responses import CreatedResult, OkResult
from app.validators.receipt_item_validators import (
    validate_receipt_item_create_data,
    validate_receipt_item_update_data,
)


def _serialize_receipt_item(item: ReceiptItem) -> dict:
    return {
        "id": str(item.id),
        "receipt_id": str(item.receipt_id),
        "user_id": str(item.user_id),
        "category_id": str(item.category_id) if item.category_id else None,
        "name": item.name,
        "quantity": float(item.quantity),
        "unit_price": float(item.unit_price),
        "total_price": float(item.total_price),
        "extra_metadata": item.extra_metadata,
    }


def _receipt_query_for_user(user_id: uuid.UUID):
    return db.session.query(Receipt).filter(Receipt.user_id == user_id)


def get_items_by_receipt(receipt_id: uuid.UUID, user_id: uuid.UUID) -> OkResult:
    receipt = _get_receipt_for_user(receipt_id, user_id)
    items = db.session.query(ReceiptItem).filter_by(receipt_id=receipt.id, user_id=user_id).all()
    return OkResult([_serialize_receipt_item(item) for item in items])


def create_item(receipt_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> CreatedResult:
    receipt = _get_receipt_for_user(receipt_id, user_id=user_id)
    validated = validate_receipt_item_create_data(data)
    category = _load_category_for_user(user_id, validated["category_id"])

    item = ReceiptItem(
        receipt_id=receipt.id,
        user_id=receipt.user_id,
        category_id=category.id if category else None,
        name=validated["name"],
        quantity=validated["quantity"],
        unit_price=validated["unit_price"],
        total_price=validated["quantity"] * validated["unit_price"],
        extra_metadata=validated["extra_metadata"],
    )

    try:
        _register_category_assigned(category)
        db.session.add(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return CreatedResult({"item_id": str(item.id), "message": "Item created successfully"})


def update_item(
    receipt_id: uuid.UUID,
    item_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
) -> OkResult:

    receipt = _get_receipt_for_user(receipt_id, user_id, lock=True)
    item = _get_item_for_user(receipt.id, item_id, user_id)
    validated = validate_receipt_item_update_data(data)
    old_category = _load_category_for_user(user_id, item.category_id)
    new_category = old_category

    if "category_id" in validated:
        new_category = _load_category_for_user(user_id, validated["category_id"])
        item.category_id = new_category.id if new_category else None

    if "name" in validated:
        item.name = validated["name"]
    if "quantity" in validated:
        item.quantity = validated["quantity"]
    if "unit_price" in validated:
        item.unit_price = validated["unit_price"]
    if "extra_metadata" in validated:
        item.extra_metadata = validated["extra_metadata"]

    item.total_price = item.quantity * item.unit_price

    try:
        if "category_id" in validated and old_category != new_category:
            _register_category_unassigned(old_category)
            _register_category_assigned(new_category)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult({"item_id": str(item.id), "message": "Item updated successfully"})


def delete_item(receipt_id: uuid.UUID, item_id: uuid.UUID, user_id: uuid.UUID) -> OkResult:
    receipt = _get_receipt_for_user(receipt_id, user_id, lock=True)
    item = _get_item_for_user(receipt.id, item_id, user_id)
    category = _load_category_for_user(user_id, item.category_id)

    try:
        _register_category_unassigned(category)
        db.session.delete(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult({"message": "Item deleted successfully"})


def _get_receipt_for_user(receipt_id: uuid.UUID, user_id: uuid.UUID, lock: bool = False) -> Receipt:
    query = _receipt_query_for_user(user_id).filter(Receipt.id == receipt_id)
    if lock:
        query = query.with_for_update()

    receipt = query.first()
    if receipt is None:
        raise NotFoundError("Receipt not found")

    return receipt


def _get_item_for_user(receipt_id: uuid.UUID, item_id: uuid.UUID, user_id: uuid.UUID) -> ReceiptItem:
    item = (
        db.session.query(ReceiptItem)
        .filter_by(id=item_id, receipt_id=receipt_id, user_id=user_id)
        .first()
    )
    if item is None:
        raise NotFoundError("Item not found")
    return item


def _load_category_for_user(user_id: uuid.UUID, category_id: uuid.UUID | None) -> Category | None:
    if category_id is None:
        return None

    category = db.session.get(Category, category_id)
    if not category or (category.user_id is not None and category.user_id != user_id):
        raise NotFoundError("Category not found")
    return category


def _register_category_assigned(category: Category | None) -> None:
    if category is None:
        return

    category.count = (category.count or 0) + 1


def _register_category_unassigned(category: Category | None) -> None:
    if category is None:
        return

    if category.count > 0:
        category.count -= 1
