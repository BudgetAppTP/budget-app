from flask import request, g

from app.api import bp
from app.services import analytics_service
from app.services.errors import BadRequestError


@bp.get("/analytics/donut", strict_slashes=False)
def api_donut_chart():
    year_raw = request.args.get("year")
    month_raw = request.args.get("month")

    try:
        year = int(year_raw) if year_raw is not None else None
        month = int(month_raw) if month_raw is not None else None
    except ValueError:
        raise BadRequestError("Invalid year/month format")

    result = analytics_service.get_donut_data(
        year=year,
        month=month,
        user_id=g.current_user.id,
    )
    return result.to_flask_response()
