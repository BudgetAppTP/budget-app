"""
Monthly Budget API

Provides an endpoint to retrieve all incomes and expenses for a specific
month. This endpoint aggregates data from the income and receipt
services and returns both the individual records and their totals for
the given month.

Path:
  - GET /api/monthly-budget?month=YYYY-MM

If the ``month`` query parameter is omitted, the current month is used.
"""

from __future__ import annotations

from flask import request
from app.api import bp, make_response
from app.services import monthly_budget_service


@bp.get("/monthly-budget", strict_slashes=False)
def api_monthly_budget_get():
    """
    GET /api/monthly-budget
    Summary: Get all incomes and expenses for a month

    Query:
      - month: "YYYY-MM" (optional; defaults to the current month)

    Responses:
      200:
        data:
          {
            "month": "YYYY-MM",
            "incomes": [...],
            "expenses": [...],
            "total_income": number,
            "total_expense": number
          }
        error: null
      400:
        data: {"error": "Invalid month format, expected YYYY-MM"}
        error: null
    """
    month_param = request.args.get("month")
    data, status = monthly_budget_service.get_monthly_summary(month_param)
    # If service returns error, wrap in error envelope
    if "error" in data:
        return make_response(None, {"code": "bad_request", "message": data["error"]}, status)
    return make_response(data, None, status)
