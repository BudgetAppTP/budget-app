"""
Analytics API

Paths:
  - GET /api/analytics/donut
"""

from flask import request, g

from app.api import bp
from app.services import analytics_service
from app.validators.common_validators import parse_month_year_query_filter


@bp.get("/analytics/donut", strict_slashes=False)
def api_donut_chart():
    month_filter = parse_month_year_query_filter(
        request.args.get("year"),
        request.args.get("month"),
    )

    result = analytics_service.get_donut_data(
        month_filter=month_filter,
        user_id=g.current_user.id,
    )
    return result.to_flask_response()
