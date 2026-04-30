"""
Dashboard API

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
from app.services.errors import BadRequestError


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
    year_raw = request.args.get("year")
    month_raw = request.args.get("month")

    try:
        year = int(year_raw) if year_raw is not None else None
        month = int(month_raw) if month_raw is not None else None
    except ValueError:
        raise BadRequestError("Invalid year/month format")

    result = dashboard_service.get_month_summary(
        year=year,
        month=month,
        user_id=g.current_user.id,
    )
    return result.to_flask_response()
