import uuid
from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Category

def get_all_categories():
    categories = db.session.query(Category).all()
    result = []
    for category in categories:
        result.append({
            "id": str(category.id),
            "user_id": str(category.user_id),
            "parent_id": str(category.parent_id) if category.parent_id is not None else None,
            "name": category.name,
            "created_at": category.created_at.isoformat() if category.created_at else None
        })

    return {
        "success": True,
        "categories": result,
    }, 200

def create_category(data: dict):
    try:

        user_id = data.get("user_id")
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        parent_id = data.get("parent_id")
        if isinstance(parent_id, str):
            parent_id = uuid.UUID(parent_id)

        category = Category(
            user_id=user_id,
            parent_id=parent_id,
            name=data.get("name")
        )

        db.session.add(category)
        db.session.commit()

        return {"id": str(category.id), "message": "Category created successfully"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
    
def update_income(category_id: uuid.UUID, data: dict):
    try:
        category = db.session.get(Category, category_id)
        if not category:
            return {"error": "Category not found"}, 404
        if "name" in data:
            category.name = data["name"]
        db.session.commit()
        return {"message": "Category updated successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
    
def delete_category(category_id: uuid.UUID):
    category = db.session.get(Category, category_id)
    if not category:
        return {"error": "Category not found"}, 404
    try:
        db.session.delete(category)
        db.session.commit()
        return {"message": "Category deleted successfully"}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400