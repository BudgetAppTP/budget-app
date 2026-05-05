"""
Monthly Budget API

Paths:
  - GET /api/monthly-budget

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  MonthlyBudget:
    {
      "month": "YYYY-MM",
      "incomes": [object],
      "expenses": [object],
      "total_income": float,
      "total_expense": float,
      "balance": float
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
"""

from flask import g, request

from app.api import bp
from app.services import monthly_budget_service
from app.validators.common_validators import parse_month_year_query_filter


@bp.get("/monthly-budget", strict_slashes=False)
def api_monthly_budget_get():
    """
    Return monthly income and expense details for the authenticated user.

    Query:
      year: int | omitted
      month: int | omitted

    Responses:
      200: {"data": MonthlyBudget, "error": null}
      400: see module errors
    """
    month_filter = parse_month_year_query_filter(
        request.args.get("year"),
        request.args.get("month"),
    )
    result = monthly_budget_service.get_month_summary_budget(
        user_id=g.current_user.id,
        month_filter=month_filter,
    )
    return result.to_flask_response()
