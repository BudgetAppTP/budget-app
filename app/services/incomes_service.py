import uuid
from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Income, Tag
from app.services import tags_service


def get_all_incomes():
    incomes = db.session.query(Income).all()
    result = []
    for inc in incomes:
        result.append({
            "id": str(inc.id),
            "user_id": str(inc.user_id),
            "tag": inc.tag.name if inc.tag else None,
            "tag_id": str(inc.tag_id) if inc.tag_id else None,
            "description": getattr(inc, "description", None),
            "amount": float(inc.amount) if inc.amount is not None else None,
            "income_date": inc.income_date.isoformat() if inc.income_date else None,
            "extra_metadata": inc.extra_metadata
        })

    total_amount = sum(
        (float(inc["amount"]) for inc in result if inc["amount"] is not None),
        0.0
    )

    return {
        "success": True,
        "incomes": result,
        "total_amount": total_amount
    }, 200

def _parse_user_id(raw_user_id):
    if isinstance(raw_user_id, uuid.UUID):
        return raw_user_id
    if isinstance(raw_user_id, str):
        return uuid.UUID(raw_user_id)
    raise ValueError("Invalid user_id format")


def _load_tag_for_income(user_id: uuid.UUID, raw_tag_id: str | None):
    """
    Validate and load tag for income for given user.

    Returns:
      (tag: Tag | None, error_body: dict | None, status: int | None)
    """
    if not raw_tag_id:
        return None, None, None

    try:
        tag_uuid = uuid.UUID(raw_tag_id)
    except ValueError:
        return None, {"error": "Invalid tag_id format"}, 400

    tag = db.session.get(Tag, tag_uuid)
    if not tag:
        return None, {"error": "Tag not found"}, 404

    if tag.user_id != user_id:
        return None, {"error": "Tag does not belong to this user"}, 403

    return tag, None, None


def create_income(data: dict):
    try:
        user_id = _parse_user_id(data.get("user_id"))

        tag, err, status = _load_tag_for_income(user_id, data.get("tag_id"))
        if err:
            return err, status

        description = (data.get("description") or "").strip()
        if not description:
            return {"error": "Missing description"}, 400

        income = Income(
            user_id=user_id,
            tag=tag,
            description=description,
            amount=Decimal(str(data.get("amount", 0))),
            income_date=date.fromisoformat(data["income_date"]) if data.get("income_date") else None,
            extra_metadata=data.get("extra_metadata")
        )

        db.session.add(income)

        if tag is not None:
            tags_service.register_tag_assigned(tag)

        db.session.commit()

        return {"id": str(income.id), "message": "Income created successfully"}, 201

    except ValueError as e:
        db.session.rollback()
        return {"error": f"Invalid data format: {str(e)}"}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def get_income_by_id(income_id: uuid.UUID):
    income = db.session.get(Income, income_id)
    if not income:
        return {"error": "Income not found"}, 404

    return {
        "id": str(income.id),
        "user_id": str(income.user_id),
        "tag": income.tag.name if income.tag else None,
        "tag_id": str(income.tag_id) if income.tag_id else None,
        "description": getattr(income, "description", None),
        "amount": float(income.amount) if income.amount is not None else None,
        "income_date": income.income_date.isoformat() if income.income_date else None,
        "extra_metadata": income.extra_metadata
    }, 200


def update_income(income_id: uuid.UUID, data: dict):
    try:
        income = db.session.get(Income, income_id)
        if not income:
            return {"error": "Income not found"}, 404

        old_tag = income.tag
        new_tag = old_tag

        # Tag update
        if "tag_id" in data:
            raw_tag_id = data["tag_id"]
            if raw_tag_id:
                tag, err, status = _load_tag_for_income(income.user_id, raw_tag_id)
                if err:
                    return err, status
                new_tag = tag
            else:
                new_tag = None

        if new_tag is not old_tag:
            if old_tag is not None:
                income.tag = None
                tags_service.register_tag_unassigned(old_tag)

            if new_tag is not None:
                income.tag = new_tag
                tags_service.register_tag_assigned(new_tag)

        if "description" in data:
            desc = (data["description"] or "").strip()
            if not desc:
                return {"error": "Description cannot be empty"}, 400
            income.description = desc

        if "amount" in data:
            income.amount = Decimal(str(data["amount"]))

        if "income_date" in data:
            income.income_date = date.fromisoformat(data["income_date"])

        if "extra_metadata" in data:
            income.extra_metadata = data["extra_metadata"]

        db.session.commit()
        return {"id": str(income.id), "message": "Income updated successfully"}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def delete_income(income_id: uuid.UUID):
    income = db.session.get(Income, income_id)
    if not income:
        return {"error": "Income not found"}, 404

    try:
        tag = income.tag

        db.session.delete(income)

        if tag is not None:
            tags_service.register_tag_unassigned(tag)

        db.session.commit()
        return {"message": "Income deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400