import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy import or_

from app.extensions import db
from app.models import Category, Receipt, ReceiptItem

def get_all_categories(user_id: uuid.UUID | None = None):
    # Order pinned categories first, then unpinned; within each group sort by usage count (highest first)
    query = db.session.query(Category)
    if user_id is not None:
        query = query.filter(or_(Category.user_id == user_id, Category.user_id.is_(None)))
    categories = query.order_by(Category.is_pinned.desc(), Category.count.desc()).all()
    result = []
    for category in categories:
        result.append({
            "id": str(category.id),
            "user_id": str(category.user_id),
            "parent_id": str(category.parent_id) if category.parent_id is not None else None,
            "name": category.name,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "count": category.count,
            "is_pinned": category.is_pinned,
            "limit": float(category.limit) if category.limit is not None else None,
        })

    return {
        "success": True,
        "categories": result,
    }, 200

def create_category(data: dict, user_id: uuid.UUID | None = None):
    try:

        if user_id is None:
            user_id = data.get("user_id")
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

        parent_id = data.get("parent_id")
        if isinstance(parent_id, str):
            parent_id = uuid.UUID(parent_id)
        
        count = data.get("count", 0)

        is_pinned = data.get("is_pinned", False)
        limit = data.get("limit")
        if limit is not None:
            limit = Decimal(str(limit))

        category = Category(
            user_id=user_id,
            parent_id=parent_id,
            name=data.get("name"),
            count=count,
            is_pinned=is_pinned,
            limit=limit,
        )

        db.session.add(category)
        db.session.commit()

        return {"id": str(category.id), "message": "Category created successfully"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
    
def update_category(category_id: uuid.UUID, data: dict, user_id: uuid.UUID | None = None):
    try:
        category = db.session.get(Category, category_id)
        if not category:
            return {"error": "Category not found"}, 404
        if user_id is not None and category.user_id != user_id:
            return {"error": "Category not found"}, 404
        if "name" in data:
            category.name = data["name"]
        if "is_pinned" in data:
            category.is_pinned = data["is_pinned"]
        if "count" in data:
            category.count = int(data["count"])
        if "limit" in data:
            raw_limit = data["limit"]
            category.limit = Decimal(str(raw_limit)) if raw_limit is not None else None
        db.session.commit()
        return {"message": "Category updated successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def get_category_monthly_limit(category_id: uuid.UUID, year: int, month: int, user_id: uuid.UUID | None = None):
    if month < 1 or month > 12:
        return {"error": "Month must be between 1 and 12"}, 400

    category = db.session.get(Category, category_id)
    if not category:
        return {"error": "Category not found"}, 404
    if user_id is not None and category.user_id not in (None, user_id):
        return {"error": "Category not found"}, 404

    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    spent_q = (
        db.session.query(func.coalesce(func.sum(ReceiptItem.total_price), 0))
        .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
        .filter(
            ReceiptItem.category_id == category_id,
            Receipt.issue_date >= start,
            Receipt.issue_date < end,
        )
    )
    if user_id is not None:
        spent_q = spent_q.filter(Receipt.user_id == user_id)

    spent = round(float(spent_q.scalar() or 0), 2)

    return {
        "year": year,
        "month": month,
        "category_id": str(category_id),
        "spent": spent,
        "limit": float(category.limit) if category.limit is not None else None,
    }, 200
    
def delete_category(category_id: uuid.UUID, user_id: uuid.UUID | None = None):
    category = db.session.get(Category, category_id)
    if not category:
        return {"error": "Category not found"}, 404
    if user_id is not None and category.user_id != user_id:
        return {"error": "Category not found"}, 404
    try:
        db.session.delete(category)
        db.session.commit()
        return {"message": "Category deleted successfully"}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
