import uuid

from app.extensions import db
from app.models import Income, Tag
from app.services import tags_service
from app.services.errors import BadRequestError, ForbiddenError, NotFoundError
from app.services.responses import CreatedResult, OkResult
from app.validators.common_validators import validate_month_year_filter
from app.validators.income_validators import (
    validate_income_create_data,
    validate_income_update_data,
)

ALLOWED_INCOME_SORT_FIELDS = {
    "income_date": Income.income_date,
    "amount": Income.amount,
}


def _serialize_income(income: Income) -> dict:
    return {
        "id": str(income.id),
        "user_id": str(income.user_id),
        "tag": income.tag.name if income.tag else None,
        "tag_id": str(income.tag_id) if income.tag_id else None,
        "description": getattr(income, "description", None),
        "amount": float(income.amount) if income.amount is not None else None,
        "income_date": income.income_date.isoformat() if income.income_date else None,
        "extra_metadata": income.extra_metadata,
    }


def _load_tag_for_income(user_id: uuid.UUID, tag_id: uuid.UUID | None):
    if tag_id is None:
        return None

    tag = db.session.get(Tag, tag_id)
    if not tag:
        raise NotFoundError("Tag not found")

    if tag.user_id != user_id:
        raise ForbiddenError("Tag does not belong to this user")

    return tag


def _get_owned_income(income_id: uuid.UUID, user_id: uuid.UUID) -> Income:
    income = db.session.get(Income, income_id)
    if not income or income.user_id != user_id:
        raise NotFoundError("Income not found")
    return income


def get_all_incomes(
    user_id: uuid.UUID,
    year: int | None = None,
    month: int | None = None,
    sort_by: str = "income_date",
    descending: bool = True,
):
    if sort_by not in ALLOWED_INCOME_SORT_FIELDS:
        raise BadRequestError("Invalid sort field")

    query = db.session.query(Income).filter(Income.user_id == user_id)

    start, end = validate_month_year_filter(year, month)
    if start is not None and end is not None:
        query = query.filter(
            Income.income_date.isnot(None),
            Income.income_date >= start,
            Income.income_date < end,
        )

    order_column = ALLOWED_INCOME_SORT_FIELDS[sort_by]
    query = query.order_by(order_column.desc() if descending else order_column.asc())

    incomes = query.all()
    payload = {
        "success": True,
        "incomes": [_serialize_income(income) for income in incomes],
        "total_amount": sum(
            float(income.amount) for income in incomes if income.amount is not None
        ),
    }
    return OkResult(payload)


def create_income(data: dict, user_id: uuid.UUID):
    validated = validate_income_create_data(data)

    tag = _load_tag_for_income(user_id, validated.get("tag_id"))

    income = Income(
        user_id=user_id,
        tag=tag,
        description=validated["description"],
        amount=validated["amount"],
        income_date=validated["income_date"],
        extra_metadata=validated["extra_metadata"],
    )

    try:
        db.session.add(income)

        if tag is not None:
            tags_service.register_tag_assigned(tag)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return CreatedResult({"id": str(income.id), "message": "Income created successfully"})


def get_income_by_id(income_id: uuid.UUID, user_id: uuid.UUID):
    income = _get_owned_income(income_id, user_id=user_id)
    return OkResult(_serialize_income(income))


def update_income(income_id: uuid.UUID, data: dict, user_id: uuid.UUID):
    income = _get_owned_income(income_id, user_id=user_id)
    validated = validate_income_update_data(data)

    new_tag, old_tag = income.tag, income.tag

    if "tag_id" in validated:
        new_tag = _load_tag_for_income(income.user_id, validated["tag_id"])

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

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult({"id": str(income.id), "message": "Income updated successfully"})


def delete_income(income_id: uuid.UUID, user_id: uuid.UUID):
    income = _get_owned_income(income_id, user_id=user_id)
    tag = income.tag

    try:
        db.session.delete(income)

        if tag is not None:
            tags_service.register_tag_unassigned(tag)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult({"message": "Income deleted successfully"})
