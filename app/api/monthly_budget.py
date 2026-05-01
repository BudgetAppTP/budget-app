"""
Monthly Budget API

Paths:
  - GET /api/monthly-budget
"""

import uuid
from flask import request
from app.api import bp, make_response
from app.services import monthly_budget_service


@bp.get("/monthly-budget", strict_slashes=False)
def api_monthly_budget_get():
    """
    GET /api/monthly-budget
    Query (optional):
      - month: YYYY-MM
      - user_id: uuid (optional)

    Behavior:
      - if month missing -> use current month
    """
    month = request.args.get("month")
    user_raw = request.args.get("user_id")

    user_id = None

    if user_raw:
        try:
            user_id = uuid.UUID(user_raw)
        except ValueError:
            return make_response(
                None,
                {"code": "validation_error", "message": "Invalid user_id format"},
                400,
            )

    data, status = monthly_budget_service.get_month_summary_budget(month=month, user_id=user_id)

    if status != 200:
        return make_response(
            None,
            {"code": "validation_error", "message": data.get("error", "Validation error")},
            status,
        )

    return make_response(data, None, status)
