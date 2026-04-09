import uuid
import re
from datetime import date

from app.extensions import db
from app.models import Income, Receipt


def get_month_summary_budget(month: str | None = None, user_id: uuid.UUID | None = None):
    """
    Return incomes and expenses for selected month in YYYY-MM format.

    If month is not provided -> use current month.
    """

    # default current month
    if month is None or not str(month).strip():
        month = date.today().strftime("%Y-%m")
    else:
        month = str(month).strip()

    # validate format YYYY-MM
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        return {"error": "Invalid month format, expected YYYY-MM"}, 400

    year = int(month[:4])
    month_num = int(month[5:7])

    if month_num < 1 or month_num > 12:
        return {"error": "Month must be between 01 and 12"}, 400

    start = date(year, month_num, 1)
    end = date(year + 1, 1, 1) if month_num == 12 else date(year, month_num + 1, 1)

    # load incomes for the month
    incomes_q = db.session.query(Income).filter(
        Income.income_date.isnot(None),
        Income.income_date >= start,
        Income.income_date < end,
    )
    if user_id is not None:
        incomes_q = incomes_q.filter(Income.user_id == user_id)

    incomes = incomes_q.order_by(Income.income_date.asc()).all()

    # load receipts(expenses) for the month
    receipts_q = db.session.query(Receipt).filter(
        Receipt.issue_date.isnot(None),
        Receipt.issue_date >= start,
        Receipt.issue_date < end,
    )
    if user_id is not None:
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

    return {
        "month": month,
        "incomes": incomes_data,
        "expenses": expenses_data,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
    }, 200