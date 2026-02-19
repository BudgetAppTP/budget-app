import uuid
from flask import request
from app.api import bp, make_response
from app.services import analytics_service

@bp.get("/analytics/donut", strict_slashes=False)
def api_donut_chart():
    year_raw = request.args.get("year")
    month_raw = request.args.get("month")
    user_raw = request.args.get("user_id")  # optional

    try:
        year = int(year_raw) if year_raw is not None else None
        month = int(month_raw) if month_raw is not None else None
    except ValueError:
        return make_response({"error": "Invalid year/month format"}, None, 400)

    user_id = None
    if user_raw:
        try:
            user_id = uuid.UUID(user_raw)
        except ValueError:
            return make_response({"error": "Invalid user_id format"}, None, 400)

    data, status = analytics_service.get_donut_data(year=year, month=month, user_id=user_id)
    return make_response(data, None, status)
