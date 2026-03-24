"""
Monthly Budget Service

Provides functionality to fetch all incomes and expenses for a given month.

The service aggregates data from existing income and receipt services and
returns a unified summary for the specified month (YYYY-MM).  When no
month is provided it defaults to the current month.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import List, Tuple, Dict, Any

from app.services import incomes_service, receipts_service


def _current_month() -> str:
    """Return the current month in YYYY-MM format."""
    return date.today().strftime("%Y-%m")


def _validate_month(month: str) -> bool:
    """Check if provided month is in YYYY-MM format."""
    return bool(re.fullmatch(r"\d{4}-\d{2}", month))


def get_monthly_summary(month: str | None = None) -> Tuple[Dict[str, Any], int]:
    """Return all incomes and expenses for a given month.

    Args:
        month: The month in "YYYY-MM" format. Defaults to current month if None.

    Returns:
        A tuple of (payload dict, HTTP status code).

    Payload example:
        {
            "month": "2025-10",
            "incomes": [...],
            "expenses": [...],
            "total_income": 123.45,
            "total_expense": 67.89
        }
    """
    target_month = (month or _current_month()).strip()

    if not _validate_month(target_month):
        return {"error": "Invalid month format, expected YYYY-MM"}, 400

    # Fetch all incomes via incomes_service
    income_data, inc_status = incomes_service.get_all_incomes()
    if inc_status != 200:
        # propagate error from service
        return income_data, inc_status
    incomes: List[Dict[str, Any]] = income_data.get("incomes", [])

    # Filter incomes by target month
    filtered_incomes: List[Dict[str, Any]] = []
    total_income = Decimal("0.00")
    for inc in incomes:
        inc_date = inc.get("income_date")
        if inc_date and inc_date.startswith(target_month):
            filtered_incomes.append(inc)
            amt = inc.get("amount")
            if amt is not None:
                try:
                    total_income += Decimal(str(amt))
                except Exception:
                    pass

    # Fetch all receipts via receipts_service
    receipt_data, rec_status = receipts_service.get_all_receipts()
    if rec_status != 200:
        return receipt_data, rec_status
    if not isinstance(receipt_data, list):
        return {"error": "Invalid receipts payload"}, 500
    receipts: List[Dict[str, Any]] = receipt_data

    # Filter receipts by target month
    filtered_expenses: List[Dict[str, Any]] = []
    total_expense = Decimal("0.00")
    for rec in receipts:
        issue_date = rec.get("issue_date")
        if issue_date and issue_date.startswith(target_month):
            filtered_expenses.append(rec)
            amt = rec.get("total_amount")
            if amt is not None:
                try:
                    total_expense += Decimal(str(amt))
                except Exception:
                    pass

    payload: Dict[str, Any] = {
        "month": target_month,
        "incomes": filtered_incomes,
        "expenses": filtered_expenses,
        "total_income": float(total_income),
        "total_expense": float(total_expense),
    }
    return payload, 200
