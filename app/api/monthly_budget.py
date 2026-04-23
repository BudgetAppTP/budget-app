from flask import g, request
from app.api import bp, make_response
from app.services import monthly_budget_service


@bp.get("/monthly-budget", strict_slashes=False)
def api_monthly_budget_get():
    """
    GET /api/monthly-budget
    Query (optional):
      - month: YYYY-MM

    Behavior:
      - if month missing -> use current month
    """
    month = request.args.get("month")

    data, status = monthly_budget_service.get_month_summary_budget(month=month, user_id=g.current_user.id)

    if status != 200:
        return make_response(
            None,
            {"code": "validation_error", "message": data.get("error", "Validation error")},
            status,
        )

    return make_response(data, None, status)
