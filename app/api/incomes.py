"""
Incomes API

Paths (Swagger-aligned):
  - GET  /api/incomes/        (list with optional sorting)   [strict_slashes=False]
  - POST /api/incomes/        (create)
  - GET  /api/incomes/{id}    (get by id)
  - PUT  /api/incomes/{id}    (update)
  - DELETE /api/incomes/{id}  (delete)

Swagger examples show raw JSON objects like:
  { "success": true, "incomes": [...], "total_amount": 1400.0 }

Actual API returns the same payload in "data" field:
  { "data": { "success": true, "incomes": [...], "total_amount": 1400.0 }, "error": null }
"""
import uuid

from flask import request
from app.api import bp, make_response
from app.services import incomes_service, tags_service


@bp.get("/incomes", strict_slashes=False)
def api_incomes_list():
    """
    GET /api/incomes/
    Summary: List incomes with optional sorting and optional month/year filter

    Query:
      - sort: "income_date" | "amount" (default: "income_date")
      - order: "asc" | "desc" (default: "desc")
      - year: YYYY (optional, must be provided вместе с month)
      - month: 1..12 (optional, must be provided вместе с year)

    Notes:
      - If year+month are provided, endpoint returns only incomes from that month/year.

    Responses:
      200:
        data:
          {
            "success": true,
            "incomes": [...],
            "total_amount": number
          }
        error: null

      400:
        - If query params are invalid:
          data:
            { "error": "Both year and month must be provided together"
              | "Month must be between 1 and 12"
            }
          error: null
    """
    sort_by = request.args.get("sort", "income_date")
    order = request.args.get("order", "desc")
    reverse = order.lower() == "desc"

    year_raw = request.args.get("year")
    month_raw = request.args.get("month")

    year = None
    month = None

    # Parse year/month if provided
    try:
        if year_raw is not None:
            year = int(year_raw)
        if month_raw is not None:
            month = int(month_raw)
    except ValueError:
        return make_response({"error": "Invalid year/month format"}, None, 400)

    data, status = incomes_service.get_all_incomes(year=year, month=month)

    if status != 200:
        return make_response(data, None, status)

    incomes_list = data.get("incomes", [])
    try:
        incomes_list.sort(key=lambda i: i[sort_by], reverse=reverse)
    except Exception:
        pass
    data["incomes"] = incomes_list
    return make_response(data, None, status)


@bp.post("/incomes", strict_slashes=False)
def api_incomes_create():
    """
    POST /api/incomes/
    Summary: Create income

    Request (JSON example):
      {
        "user_id": "<uuid>",               # required
        "income_date": "YYYY-MM-DD",       # optional (can be null/omitted)
        "description": "Freelance projekt",# required, non-empty string
        "amount": 500.00,                  # optional, defaults to 0 if missing
        "tag_id": "<uuid>",                # optional, must belong to the same user
        "extra_metadata": { ... }          # optional JSON
      }

    Responses:
      201:
        data:
          {
            "id": "<uuid>",
            "message": "Income created successfully"
          }
        error: null

      400:
        data:
          {
            "error": "Missing description"
              | "Invalid user_id format"
              | "Invalid tag_id format"
              | "Tag not found"
              | "Tag does not belong to this user"
              | "Invalid data format: ..."
          }
        error: null
    """
    payload = request.get_json(force=True) or {}
    response, status = incomes_service.create_income(payload)
    return make_response(response, None, status)


@bp.get("/incomes/<uuid:income_id>", strict_slashes=False)
def api_incomes_get(income_id):
    """
    GET /api/incomes/{income_id}
    Summary: Get income by id

    Path:
      income_id: uuid

    Responses:
      200:
        data:
          {
            "id": "<uuid>",
            "user_id": "<uuid>",
            "tag": "Salary" | null,
            "tag_id": "<uuid>" | null,
            "description": "Freelance projekt",
            "amount": number,
            "income_date": "YYYY-MM-DD" | null,
            "extra_metadata": { ... } | null
          }
        error: null

      404:
        data:
          {
            "error": "Income not found"
          }
        error: null
    """
    response, status = incomes_service.get_income_by_id(income_id)
    return make_response(response, None, status)


@bp.put("/incomes/<uuid:income_id>", strict_slashes=False)
def api_incomes_update(income_id):
    """
    PUT /api/incomes/{income_id}
    Summary: Update income

    Path:
      income_id: uuid

    Request (JSON example):
      {
        "income_date": "YYYY-MM-DD",       # optional
        "description": "Updated description",  # optional, if present must be non-empty
        "amount": 600.00,                  # optional
        "tag_id": "<uuid>",                # optional (null to detach tag)
        "extra_metadata": { ... }          # optional
      }

    Responses:
      200:
        data:
          {
            "id": "<uuid>",
            "message": "Income updated successfully"
          }
        error: null

      400:
        - If body is missing:
          data: null
          error: {"code":"bad_request","message":"Missing JSON body"}

        - If validation fails (e.g. empty description, invalid tag/user):
          data:
            {
              "error": "Description cannot be empty"
                | "Invalid tag_id format"
                | "Tag not found"
                | "Tag does not belong to this user"
            }
          error: null

      404:
        data:
          {
            "error": "Income not found"
          }
        error: null
    """
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = incomes_service.update_income(income_id, payload)
    return make_response(response, None, status)


@bp.delete("/incomes/<uuid:income_id>", strict_slashes=False)
def api_incomes_delete(income_id):
    """
    DELETE /api/incomes/{income_id}
    Summary: Delete income

    Path:
      income_id: uuid

    Responses:
      200:
        data:
          {
            "message": "Income deleted successfully"
          }
        error: null

      404:
        data:
          {
            "error": "Income not found"
          }
        error: null
    """
    response, status = incomes_service.delete_income(income_id)
    return make_response(response, None, status)


@bp.get("/incomes/tags", strict_slashes=False)
def api_income_tags_list():
    """
    GET /api/incomes/tags
    Summary: Get all income-related tags (type=INCOME or BOTH)

    Query (optional):
      - user_id: uuid (if provided, returns only tags of that user)

    Responses:
      200:
        data:
          {
            "success": true,
            "tags": [
              {
                "id": "<uuid>",
                "user_id": "<uuid>",
                "name": "Salary",
                "type": "INCOME" | "BOTH",
                "counter": number
              },
              ...
            ]
          }
        error: null

      400:
        - If user_id format is invalid:
          data:
            { "error": "Invalid user_id format" }
          error: null
    """
    raw_user_id = request.args.get("user_id")
    user_id = None

    if raw_user_id:
        try:
            user_id = uuid.UUID(raw_user_id)
        except ValueError:
            return make_response({"error": "Invalid user_id format"}, None, 400)

    data, status = tags_service.get_income_tags(user_id=user_id)
    return make_response(data, None, status)