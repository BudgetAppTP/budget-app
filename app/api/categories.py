"""
Categories API

Paths:
  - GET    /api/categories
  - POST   /api/categories
  - GET    /api/categories/monthly-limit
  - PUT    /api/categories/{category_id}
  - DELETE /api/categories/{category_id}

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  Category:
    {
      "id": uuid,
      "user_id": "uuid | null",
      "parent_id": "uuid | null",
      "name": str,
      "created_at": "ISO8601 | null",
      "count": int,
      "is_pinned": bool,
      "limit": "float | null"
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
"""

import uuid

from flask import g, request

from app.api import bp
from app.api.request_parsing import parse_json_object_body
from app.services import categories_service
from app.services.errors import BadRequestError
from app.validators.common_validators import parse_month_year_query_filter


@bp.get("/categories", strict_slashes=False)
def api_categories_list():
    """
    List categories owned by the current user plus shared categories.

    Responses:
      200: {"data": {"success": true, "categories": [Category]}, "error": null}
    """
    result = categories_service.get_all_categories(g.current_user.id)
    return result.to_flask_response()


@bp.post("/categories", strict_slashes=False)
def create_category():
    """
    Create category for the current user.

    Request:
      {"name": str, "parent_id": "uuid|null", "limit": float?}

    Responses:
      201: {"data": {"id": uuid, "message": str}, "error": null}
      400: see module errors
      404: see module errors
    """
    payload = parse_json_object_body()

    result = categories_service.create_category(payload, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.get("/categories/monthly-limit", strict_slashes=False)
def get_category_monthly_limit():
    """
    Get spent amount and configured limit for one category in one month.

    Query:
      year: int (required)
      month: int 1..12 (required)
      category_id: uuid (required)

    Responses:
      200: {"data": {"year": int, "month": int, "category_id": uuid, "spent": float, "limit": "float | null"}, "error": null}
      400: see module errors
      404: see module errors
    """
    year_raw = request.args.get("year")
    month_raw = request.args.get("month")
    category_raw = request.args.get("category_id")

    if year_raw is None or month_raw is None or not category_raw:
        raise BadRequestError("Missing required query params: year, month, category_id")

    month_filter = parse_month_year_query_filter(year_raw, month_raw)

    try:
        category_id = uuid.UUID(category_raw)
    except ValueError:
        raise BadRequestError("Invalid category_id format")

    result = categories_service.get_category_monthly_limit(
        category_id=category_id,
        month_filter=month_filter,
        user_id=g.current_user.id,
    )
    return result.to_flask_response()


@bp.put("/categories/<uuid:category_id>", strict_slashes=False)
def update_category(category_id):
    """
    Update category owned by the current user.

    Path:
      category_id: uuid

    Request:
      {"name": str?, "is_pinned": bool?, "count": int?, "limit": float|null?}

    Responses:
      200: {"data": {"message": "Category updated successfully"}, "error": null}
      400: see module errors
      404: see module errors
    """
    payload = parse_json_object_body(allow_empty=False)

    result = categories_service.update_category(
        category_id,
        payload,
        user_id=g.current_user.id,
    )
    return result.to_flask_response()


@bp.delete("/categories/<uuid:category_id>", strict_slashes=False)
def delete_category(category_id):
    """
    Delete category owned by the current user.

    Path:
      category_id: uuid

    Responses:
      200: {"data": {"message": "Category deleted successfully"}, "error": null}
      400: see module errors
      404: see module errors
    """
    result = categories_service.delete_category(category_id, user_id=g.current_user.id)
    return result.to_flask_response()
