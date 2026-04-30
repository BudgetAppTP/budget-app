import uuid

from sqlalchemy import func, or_

from app.extensions import db
from app.models import Category, Receipt, ReceiptItem
from app.services.errors import BadRequestError, NotFoundError
from app.services.responses import CreatedResult, OkResult
from app.validators.category_validators import (
    validate_category_create_data,
    validate_category_monthly_limit_params,
    validate_category_update_data,
)


def get_all_categories(user_id: uuid.UUID):
    # Order pinned categories first, then unpinned; within each group sort by usage count (highest first)
    categories = (
        db.session.query(Category)
        .filter(or_(Category.user_id == user_id, Category.user_id.is_(None)))
        .order_by(Category.is_pinned.desc(), Category.count.desc())
        .all()
    )
    result = []
    for category in categories:
        result.append({
            "id": str(category.id),
            "user_id": str(category.user_id) if category.user_id is not None else None,
            "parent_id": str(category.parent_id) if category.parent_id is not None else None,
            "name": category.name,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "count": category.count,
            "is_pinned": category.is_pinned,
            "limit": float(category.limit) if category.limit is not None else None,
        })

    return OkResult({
        "success": True,
        "categories": result,
    })


def create_category(data: dict, user_id: uuid.UUID):
    validated, err, status = validate_category_create_data(data)
    if err:
        raise BadRequestError(err["error"], status_code=status)

    if validated["parent_id"] is not None:
        parent = db.session.get(Category, validated["parent_id"])
        if not parent or (parent.user_id is not None and parent.user_id != user_id):
            raise NotFoundError("Parent category not found")
    else:
        parent = None

    category = Category(
        user_id=user_id,
        parent_id=parent.id if parent is not None else None,
        name=validated["name"],
        count=0,
        is_pinned=False,
        limit=validated["limit"],
    )

    try:
        db.session.add(category)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return CreatedResult({"id": str(category.id), "message": "Category created successfully"})


def update_category(category_id: uuid.UUID, data: dict, user_id: uuid.UUID):
    category = db.session.get(Category, category_id)
    if not category or category.user_id != user_id:
        raise NotFoundError("Category not found")

    validated, err, status = validate_category_update_data(data)
    if err:
        raise BadRequestError(err["error"], status_code=status)

    try:
        if "name" in validated:
            category.name = validated["name"]
        if "is_pinned" in validated:
            category.is_pinned = validated["is_pinned"]
        if "count" in validated:
            category.count = validated["count"]
        if "limit" in validated:
            category.limit = validated["limit"]
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult({"message": "Category updated successfully"})


def get_category_monthly_limit(category_id: uuid.UUID, year: int, month: int, user_id: uuid.UUID):
    validated, date_range, err, status = validate_category_monthly_limit_params(
        category_id=category_id,
        year=year,
        month=month,
    )
    if err:
        raise BadRequestError(err["error"], status_code=status)

    category = db.session.get(Category, category_id)
    if not category or (category.user_id is not None and category.user_id != user_id):
        raise NotFoundError("Category not found")

    spent_q = (
        db.session.query(func.coalesce(func.sum(ReceiptItem.total_price), 0))
        .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
        .filter(
            ReceiptItem.category_id == category_id,
            Receipt.user_id == user_id,
            Receipt.issue_date >= date_range["start"],
            Receipt.issue_date < date_range["end"],
        )
    )

    spent = round(float(spent_q.scalar() or 0), 2)

    return OkResult({
        "year": validated["year"],
        "month": validated["month"],
        "category_id": str(validated["category_id"]),
        "spent": spent,
        "limit": float(category.limit) if category.limit is not None else None,
    })


def delete_category(category_id: uuid.UUID, user_id: uuid.UUID):
    category = db.session.get(Category, category_id)
    if not category or category.user_id != user_id:
        raise NotFoundError("Category not found")
    try:
        db.session.delete(category)
        db.session.commit()
        return OkResult({"message": "Category deleted successfully"})
    except Exception:
        db.session.rollback()
        raise
