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
              {"id": "...", "income_date": "YYYY-MM-DD", "description": "str", "amount": number}
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
        "user_id": "<uuid>",
        "income_date": "YYYY-MM-DD",
        "description": "Freelance projekt",
        "amount": 500.00
      }

    Responses:
      201:
        data:
          {
            "success": true,
            "income": {"id": "...", "income_date": "YYYY-MM-DD", "description": "str", "amount": number}
          }
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Invalid input data"}
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
            "success": true,
            "income": {"id":"...","income_date":"YYYY-MM-DD","description":"...","amount":number}
          }
        error: null
      404:
        data: null
        error: {"code":"not_found","message":"Income not found"}
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
        "income_date": "YYYY-MM-DD",
        "description": "Updated",
        "amount": 600.00
      }

    Responses:
      200:
        data:
          {
            "success": true,
            "income": {"id":"...","income_date":"YYYY-MM-DD","description":"Updated","amount":600.0}
          }
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Missing JSON body"}
      404:
        data: null
        error: {"code":"not_found","message":"Income not found"}
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
        data: {"success": true, "...": "..."}  # implementation defined
        error: null
      404:
        data: null
        error: {"code":"not_found","message":"Income not found"}
    """
    response, status = incomes_service.delete_income(income_id)
    return make_response(response, None, status)
