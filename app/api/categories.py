"""
Categories API

Paths (Swagger-aligned):
  - GET    /api/categories/      (list)   [strict_slashes=False]
  - POST   /api/categories/      (create)
  - PUT    /api/categories/{id}  (update)
  - DELETE /api/categories/{id}  (delete)

Swagger examples show raw JSON objects like:
  { "success": true, "categories": [...] }

Actual API returns the same payload in "data" field:
  { "data": { "success": true, "categories": [...] }, "error": null }
"""

from flask import request

from app.api import bp, make_response
from app.services import categories_service


@bp.get("/categories", strict_slashes=False)
def api_categories_list():
    """
    GET /api/categories/
    Summary: List categories

    Responses:
      200:
        data:
          {
            "success": true,
            "categories": [
              {"id": "...", "user_id": "...", "parent_id": "...|null", "name": "str", "created_at": "ISO8601|null"}
            ]
          }
        error: null
    """
    data, status = categories_service.get_all_categories()
    return make_response(data, None, status)


@bp.post("/categories", strict_slashes=False)
def create_category():
    """
    POST /api/categories/
    Summary: Create category

    Request (JSON example):
      {
        "user_id": "<uuid>",
        "parent_id": "<uuid|null>",
        "name": "Groceries"
      }

    Responses:
      201:
        data: {"id": "...", "message": "Category created successfully"}
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Invalid input data"}
    """
    # Accept JSON body (force=True allows clients that forget the Content-Type header)
    payload = request.get_json(force=True) or {}
    response, status = categories_service.create_category(payload)
    return make_response(response, None, status)


@bp.put("/categories/<uuid:category_id>", strict_slashes=False)
def update_category(category_id):
    """
    PUT /api/categories/{category_id}
    Summary: Update category

    Path:
      category_id: uuid

    Request (JSON example):
      {
        "name": "Updated name",
        "is_pinned": true,
        "count": 3
      }

    Responses:
      200:
        data: {"message": "Category updated successfully"}
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"Missing JSON body"}
      404:
        data: null
        error: {"code":"not_found","message":"Category not found"}
    """
    # Force JSON parsing so Postman/clients without Content-Type still work
    payload = request.get_json(force=True) or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)

    response, status = categories_service.update_category(category_id, payload)
    return make_response(response, None, status)


@bp.delete("/categories/<uuid:category_id>", strict_slashes=False)
def delete_category(category_id):
    """
    DELETE /api/categories/{category_id}
    Summary: Delete category

    Path:
      category_id: uuid

    Responses:
      200:
        data: {"message": "Category deleted successfully"}
        error: null
      404:
        data: null
        error: {"code":"not_found","message":"Category not found"}
    """
    response, status = categories_service.delete_category(category_id)
    return make_response(response, None, status)
