import uuid
from flask import request
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
    user_raw = request.args.get("user_id")

    year = None
    month = None
    user_id = None

    try:
        if year_raw is not None:
            year = int(year_raw)
        if month_raw is not None:
            month = int(month_raw)
    except ValueError:
        return make_response({"error": "Invalid year/month format"}, None, 400)

    if user_raw:
        try:
            user_id = uuid.UUID(user_raw)
        except ValueError:
            return make_response({"error": "Invalid user_id format"}, None, 400)

    data, status = dashboard_service.get_month_summary(year=year, month=month, user_id=user_id)
    return make_response(data, None, status)
