import uuid
from datetime import date

from sqlalchemy import func

from app.extensions import db
from app.models import Income, Receipt
from app.services.responses import OkResult
from app.validators.common_validators import MonthYearFilter, validate_month_year_filter


def get_month_summary(
    user_id: uuid.UUID,
    month_filter: MonthYearFilter,
):
    """
    Return total incomes and total expenses for selected month/year.
    If year/month are not provided -> current month.
    If only one is provided -> error (same rule as other endpoints).
    """

    # default: current month
    if month_filter.year is None and month_filter.month is None:
        today = date.today()
        month_filter = validate_month_year_filter(today.year, today.month)

    start, end = month_filter.range()

    incomes_q = db.session.query(func.coalesce(func.sum(Income.amount), 0))
    incomes_q = incomes_q.filter(
        Income.income_date.isnot(None),
        Income.income_date >= start,
        Income.income_date < end,
    )
    incomes_q = incomes_q.filter(Income.user_id == user_id)

    receipts_q = db.session.query(func.coalesce(func.sum(Receipt.total_amount), 0))
    receipts_q = receipts_q.filter(
        Receipt.issue_date >= start,
        Receipt.issue_date < end,
    )
    receipts_q = receipts_q.filter(Receipt.user_id == user_id)

    total_incomes = float(incomes_q.scalar() or 0)
    total_expenses = float(receipts_q.scalar() or 0)

    return OkResult({
        "success": True,
        "year": month_filter.year,
        "month": month_filter.month,
        "total_incomes": total_incomes,
        "total_expenses": total_expenses,
        "balance": total_incomes - total_expenses,
    })
