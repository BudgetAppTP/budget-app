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

from flask import request
from app.api import bp, make_response
from app.services import incomes_service


@bp.get("/incomes", strict_slashes=False)
def api_incomes_list():
    """
    GET /api/incomes/
    Summary: List incomes with optional sorting

    Query:
      - sort: "income_date" | "amount" (default: "income_date")
      - order: "asc" | "desc" (default: "desc")

    Responses:
      200:
        data:
          {
            "success": true,
            "incomes": [
              {
                "id": "<uuid>",
                "user_id": "<uuid>",
                "tag": "Salary" | null,
                "tag_id": "<uuid>" | null,
                "description": "Freelance projekt",
                "amount": number,
                "income_date": "YYYY-MM-DD" | null,
                "extra_metadata": { ... } | null
              },
              ...
            ],
            "total_amount": number
          }
        error: null
    """
    data, status = incomes_service.get_all_incomes()
    incomes_list = data.get("incomes", [])
    sort_by = request.args.get("sort", "income_date")
    order = request.args.get("order", "desc")
    reverse = order.lower() == "desc"
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
