"""
Incomes API

Paths:
  - GET    /api/incomes
  - POST   /api/incomes
  - GET    /api/incomes/{income_id}
  - PUT    /api/incomes/{income_id}
  - DELETE /api/incomes/{income_id}
  - GET    /api/incomes/tags

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  Income:
    {
      "id": uuid,
      "user_id": uuid,
      "tag": "str | null",
      "tag_id": "uuid | null",
      "description": str,
      "amount": float,
      "income_date": "YYYY-MM-DD | null",
      "extra_metadata": "object | null"
    }

  IncomeList:
    {
      "success": true,
      "incomes": [Income],
      "total_amount": float
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  403: {"data": null, "error": {"code": "forbidden", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
"""

import uuid

from flask import g, request

from app.api import bp
from app.api.request_parsing import parse_json_object_body
from app.services import incomes_service, tags_service
from app.validators.common_validators import parse_month_year_query_filter


@bp.get("/incomes", strict_slashes=False)
def api_incomes_list():
    """
    List incomes for the authenticated user with optional sorting and month filter.

    Query:
      sort: "income_date" | "amount" (default: "income_date")
      order: "asc" | "desc" (default: "desc")
      year: int | omitted
      month: int | omitted

    Responses:
      200: {"data": IncomeList, "error": null}
      400: see module errors
    """
    month_filter = parse_month_year_query_filter(
        request.args.get("year"),
        request.args.get("month"),
    )

    result = incomes_service.get_all_incomes(
        month_filter=month_filter,
        user_id=g.current_user.id,
        sort_by=request.args.get("sort", "income_date"),
        descending=request.args.get("order", "desc").lower() == "desc",
    )
    return result.to_flask_response()


@bp.post("/incomes", strict_slashes=False)
def api_incomes_create():
    """
    Create income for the authenticated user.

    Request:
      {
        "income_date": "YYYY-MM-DD",
        "description": str,
        "amount": float,
        "tag_id": "uuid | null",
        "extra_metadata": "object | null"
      }

    Responses:
      201: {"data": {"id": uuid, "message": str}, "error": null}
      400: see module errors
      403: see module errors
      404: see module errors
    """
    payload = parse_json_object_body()
    result = incomes_service.create_income(payload, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.get("/incomes/<uuid:income_id>", strict_slashes=False)
def api_incomes_get(income_id: uuid.UUID):
    """
    Get one income owned by the authenticated user.

    Path:
      income_id: uuid

    Responses:
      200: {"data": Income, "error": null}
      404: see module errors
    """
    result = incomes_service.get_income_by_id(income_id, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.put("/incomes/<uuid:income_id>", strict_slashes=False)
def api_incomes_update(income_id: uuid.UUID):
    """
    Update one income owned by the authenticated user.

    Path:
      income_id: uuid

    Request:
      {
        "income_date": "YYYY-MM-DD" | omitted,
        "description": "str | omitted",
        "amount": "float | omitted",
        "tag_id": "uuid | null | omitted",
        "extra_metadata": "object | null | omitted"
      }

    Responses:
      200: {"data": {"id": uuid, "message": str}, "error": null}
      400: see module errors
      403: see module errors
      404: see module errors
    """
    payload = parse_json_object_body()
    result = incomes_service.update_income(income_id, payload, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.delete("/incomes/<uuid:income_id>", strict_slashes=False)
def api_incomes_delete(income_id: uuid.UUID):
    """
    Delete one income owned by the authenticated user.

    Path:
      income_id: uuid

    Responses:
      200: {"data": {"message": str}, "error": null}
      404: see module errors
    """
    result = incomes_service.delete_income(income_id, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.get("/incomes/tags", strict_slashes=False)
def api_income_tags_list():
    """
    List income-related tags for the authenticated user.

    Responses:
      200: {"data": {"success": true, "tags": [object]}, "error": null}
    """
    result = tags_service.get_income_tags(user_id=g.current_user.id)
    return result.to_flask_response()
