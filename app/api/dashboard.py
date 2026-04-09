import uuid
from flask import request, g
from app.api import bp, make_response
from app.services import dashboard_service


@bp.get("/dashboard/summary", strict_slashes=False)
def api_dashboard_summary():
    """
    GET /api/dashboard/summary
    Query (optional):
      - year: int
      - month: int (1..12)
      - user_id: uuid (optional)

    Behavior:
      - if year+month missing -> use current month
      - if only one provided -> 400
    """
    year_raw = request.args.get("year")
    month_raw = request.args.get("month")
    year = None
    month = None

    try:
        if year_raw is not None:
            year = int(year_raw)
        if month_raw is not None:
            month = int(month_raw)
    except ValueError:
        return make_response({"error": "Invalid year/month format"}, None, 400)

    data, status = dashboard_service.get_month_summary(
        year=year,
        month=month,
        user_id=g.current_user.id,
    )
    return make_response(data, None, status)
