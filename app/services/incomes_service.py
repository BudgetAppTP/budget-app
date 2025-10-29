import uuid
from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Income


def get_all_incomes():
    incomes = db.session.query(Income).all()
    result = []
    for inc in incomes:
        result.append({
            "id": str(inc.id),
            "user_id": str(inc.user_id),
            "amount": float(inc.amount) if inc.amount is not None else None,
            "income_date": inc.income_date.isoformat() if inc.income_date else None,
            "source": inc.source,
            "extra_metadata": inc.extra_metadata
        })

    total_amount = sum((float(inc["amount"]) for inc in result if inc["amount"] is not None), 0.0)

    return {
        "success": True,
        "incomes": result,
        "total_amount": total_amount
    }, 200


def create_income(data: dict):
    try:
        user_id = data.get("user_id")
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        income = Income(
            user_id=user_id,
            amount=Decimal(str(data.get("amount", 0))),
            income_date=date.fromisoformat(data["income_date"]) if data.get("income_date") else None,
            source=data.get("source"),
            extra_metadata=data.get("extra_metadata")
        )

        db.session.add(income)
        db.session.commit()

        return {"id": str(income.id), "message": "Income created successfully"}, 201

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
        "amount": float(income.amount) if income.amount is not None else None,
        "income_date": income.income_date.isoformat() if income.income_date else None,
        "source": income.source,
        "extra_metadata": income.extra_metadata
    }, 200


def update_income(income_id: uuid.UUID, data: dict):
    try:
        income = db.session.get(Income, income_id)
        if not income:
            return {"error": "Income not found"}, 404

        if "amount" in data:
            income.amount = Decimal(str(data["amount"]))
        if "income_date" in data:
            income.income_date = date.fromisoformat(data["income_date"])
        if "source" in data:
            income.source = data["source"]
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
        db.session.delete(income)
        db.session.commit()
        return {"message": "Income deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400