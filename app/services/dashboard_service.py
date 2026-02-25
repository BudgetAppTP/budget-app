import uuid
from datetime import date

from sqlalchemy import func
from app.extensions import db
from app.models import Income, Receipt


def get_month_summary(
    year: int | None = None,
    month: int | None = None,
    user_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
):
    """
    Return total incomes and total expenses for selected month/year.
    If year/month are not provided -> current month.
    If only one is provided -> error (same rule as other endpoints).
    """

    # default: current month
    if year is None and month is None:
        today = date.today()
        year = today.year
        month = today.month

    # validation (same as others)
    if (year is None) ^ (month is None):
        return {"error": "Both year and month must be provided together"}, 400

    if month < 1 or month > 12:
        return {"error": "Month must be between 1 and 12"}, 400

    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    incomes_q = db.session.query(func.coalesce(func.sum(Income.amount), 0))
    incomes_q = incomes_q.filter(
        Income.income_date.isnot(None),
        Income.income_date >= start,
        Income.income_date < end,
    )
    if user_id is not None:
        incomes_q = incomes_q.filter(Income.user_id == user_id)

    receipts_q = db.session.query(func.coalesce(func.sum(Receipt.total_amount), 0))
    receipts_q = receipts_q.filter(
        Receipt.issue_date >= start,
        Receipt.issue_date < end,
    )
    if user_id is not None:
        receipts_q = receipts_q.filter(Receipt.user_id == user_id)
    if account_id is not None:
        receipts_q = receipts_q.filter(Receipt.account_id == account_id)

    total_incomes = float(incomes_q.scalar() or 0)
    total_expenses = float(receipts_q.scalar() or 0)

    return {
        "success": True,
        "year": year,
        "month": month,
        "total_incomes": total_incomes,
        "total_expenses": total_expenses,
        "balance": total_incomes - total_expenses,
    }, 200
