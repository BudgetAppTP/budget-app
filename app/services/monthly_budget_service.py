import uuid
from datetime import date

from app.extensions import db
from app.models import Income, Receipt
from app.services.responses import OkResult
from app.validators.common_validators import MonthYearFilter, validate_month_year_filter


def get_month_summary_budget(
    user_id: uuid.UUID,
    month_filter: MonthYearFilter,
):
    """
    Return incomes and expenses for selected month/year.

    If year/month are not provided -> use current month.
    """
    if month_filter.year is None and month_filter.month is None:
        today = date.today()
        month_filter = validate_month_year_filter(today.year, today.month)

    start, end = month_filter.range()

    # load incomes for the month
    incomes_q = db.session.query(Income).filter(
        Income.income_date.isnot(None),
        Income.income_date >= start,
        Income.income_date < end,
    )
    incomes_q = incomes_q.filter(Income.user_id == user_id)

    incomes = incomes_q.order_by(Income.income_date.asc()).all()

    # load receipts(expenses) for the month
    receipts_q = db.session.query(Receipt).filter(
        Receipt.issue_date.isnot(None),
        Receipt.issue_date >= start,
        Receipt.issue_date < end,
    )
    receipts_q = receipts_q.filter(Receipt.user_id == user_id)

    receipts = receipts_q.order_by(Receipt.issue_date.asc()).all()

    incomes_data = []
    total_income = 0.0

    for inc in incomes:
        amount = float(inc.amount or 0)
        total_income += amount

        incomes_data.append({
            "id": str(inc.id),
            "income_date": inc.income_date.isoformat() if inc.income_date else None,
            "description": inc.description,
            "amount": amount,
        })

    expenses_data = []
    total_expense = 0.0

    for rec in receipts:
        amount = float(rec.total_amount or 0)
        total_expense += amount

        expenses_data.append({
            "id": str(rec.id),
            "issue_date": rec.issue_date.isoformat() if rec.issue_date else None,
            "category": getattr(rec, "category", None),
            "vendor": getattr(rec, "vendor", None),
            "store_name": getattr(rec, "store_name", None),
            "description": getattr(rec, "description", None),
            "total_amount": amount,
        })

    return OkResult({
        "month": f"{month_filter.year:04d}-{month_filter.month:02d}",
        "incomes": incomes_data,
        "expenses": expenses_data,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
    })
