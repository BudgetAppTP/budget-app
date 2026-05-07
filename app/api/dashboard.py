"""
Dashboard API

Paths:
  - GET /api/dashboard/summary

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  DashboardSummary:
    {
      "success": true,
      "year": int,
      "month": int,
      "total_incomes": float,
      "total_expenses": float,
      "balance": float
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
"""

from flask import g, request

from app.api import bp
from app.services import dashboard_service
from app.validators.common_validators import parse_month_year_query_filter


@bp.get("/dashboard/summary", strict_slashes=False)
def api_dashboard_summary():
    """
    Get monthly income and expense totals for the authenticated user.

    Query:
      year: int | omitted
      month: int | omitted

    Responses:
      200: {"data": DashboardSummary, "error": null}
      400: see module errors
    """
    month_filter = parse_month_year_query_filter(
        request.args.get("year"),
        request.args.get("month"),
    )

    result = dashboard_service.get_month_summary(
        month_filter=month_filter,
        user_id=g.current_user.id,
    )
    return result.to_flask_response()
