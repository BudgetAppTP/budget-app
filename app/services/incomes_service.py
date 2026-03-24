import uuid
from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Income, Tag, User
from app.services import tags_service
from app.validators.common_validators import validate_month_year_filter
from app.validators.income_validators import validate_income_create_data, validate_income_update_data


#TODO Add user filtering.
def get_all_incomes(year: int | None = None, month: int | None = None):
    """
    Get all incomes.

    Optional filtering:
      - year + month: return only incomes that belong to given month/year.

    Args:
      year: int | None
      month: int | None (1..12)

    Returns:
      tuple: (payload: dict, status_code: int)

      payload example:
        {
          "success": True,
          "incomes": [...],
          "total_amount": 1400.0
        }
    """
    query = db.session.query(Income)

    start, end, err, status = validate_month_year_filter(year, month)
    if err:
        return err, status

    if start is not None and end is not None:
        query = query.filter(
            Income.income_date.isnot(None),
            Income.income_date >= start,
            Income.income_date < end
        )

    incomes = query.all()

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
        validated, err, status = validate_income_create_data(data)
        if err:
            return err, status

        user_id = validated["user_id"]

        user = db.session.get(User, user_id)
        if not user:
            return {"error": "User not found"}, 404

        tag, err, status = _load_tag_for_income(user_id, validated.get("tag_id"))
        if err:
            return err, status

        income = Income(
            user_id=user_id,
            tag=tag,
            description=validated["description"],
            amount=validated["amount"],
            income_date=validated["income_date"],
            extra_metadata=validated["extra_metadata"]
        )

        db.session.add(income)

        if tag is not None:
            tags_service.register_tag_assigned(tag)

        db.session.commit()

        return {"id": str(income.id), "message": "Income created successfully"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400

#TODO use _get_income_for_user()
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

#TODO use _get_income_for_user()
def update_income(income_id: uuid.UUID, data: dict):
    try:
        income = db.session.get(Income, income_id)
        if not income:
            return {"error": "Income not found"}, 404

        validated, err, status = validate_income_update_data(data)
        if err:
            return err, status

        old_tag = income.tag
        new_tag = old_tag

        if "tag_id" in validated:
            raw_tag_id = validated["tag_id"]
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

        if "description" in validated:
            income.description = validated["description"]
        if "amount" in validated:
            income.amount = validated["amount"]
        if "income_date" in validated:
            income.income_date = validated["income_date"]
        if "extra_metadata" in validated:
            income.extra_metadata = validated["extra_metadata"]

        db.session.commit()
        return {"id": str(income.id), "message": "Income updated successfully"}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400

#TODO use _get_income_for_user()
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


# TODO: Use this method to ensure that users only have access to their own income and prevent them from using other users' income.
def _get_income_for_user(income_id: uuid.UUID, user_id: uuid.UUID):
    income = db.session.get(Income, income_id)
    if not income:
        return None, {"error": "Income not found"}, 404

    if income.user_id != user_id:
        return None, {"error": "Forbidden"}, 403

    return income, None, None