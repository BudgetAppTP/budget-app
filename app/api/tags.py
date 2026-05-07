"""
Tags API

Paths:
  - GET    /api/tags/income
  - GET    /api/tags/expense
  - POST   /api/tags
  - PUT    /api/tags/{tag_id}
  - DELETE /api/tags/{tag_id}

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  Tag:
    {
      "id": uuid,
      "user_id": uuid,
      "name": str,
      "type": "income | expense | both | null",
      "counter": int
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
"""

import uuid

from flask import g

from app.api import bp
from app.api.request_parsing import parse_json_object_body
from app.models.tag import TagType
from app.services import tags_service


@bp.get("/tags/income", strict_slashes=False)
def api_tags_income_list():
    """
    List income-related tags for the authenticated user.

    Responses:
      200: {"data": {"tags": [Tag], "count": int}, "error": null}
    """
    result = tags_service.get_tags_by_type(TagType.INCOME, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.get("/tags/expense", strict_slashes=False)
def api_tags_expense_list():
    """
    List expense-related tags for the authenticated user.

    Responses:
      200: {"data": {"tags": [Tag], "count": int}, "error": null}
    """
    result = tags_service.get_tags_by_type(TagType.EXPENSE, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.post("/tags", strict_slashes=False)
def api_tags_create():
    """
    Create one tag for the authenticated user.

    Request:
      {
        "user_id": "uuid | omitted | ignored",
        "name": str,
        "type": "income | expense | both | null | omitted; defaults to both"
      }

    Responses:
      201: {"data": {"id": uuid, "message": str}, "error": null}
      400: see module errors
      404: see module errors
    """
    payload = parse_json_object_body(allow_empty=False)
    result = tags_service.create_tag(payload, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.put("/tags/<uuid:tag_id>", strict_slashes=False)
def api_tags_update(tag_id: uuid.UUID):
    """
    Update one tag owned by the authenticated user.

    Path:
      tag_id: uuid

    Request:
      {
        "name": "str | omitted",
        "type": "income | expense | both | null | omitted; linked tags keep relationship-derived type"
      }

    Responses:
      200: {"data": {"id": uuid, "message": str}, "error": null}
      400: see module errors
      404: see module errors
    """
    payload = parse_json_object_body(allow_empty=False)
    result = tags_service.update_tag(tag_id, payload, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.delete("/tags/<uuid:tag_id>", strict_slashes=False)
def api_tags_delete(tag_id: uuid.UUID):
    """
    Delete one tag owned by the authenticated user.

    Path:
      tag_id: uuid

    Responses:
      200: {"data": {"message": str}, "error": null}
      404: see module errors
    """
    result = tags_service.delete_tag(tag_id, user_id=g.current_user.id)
    return result.to_flask_response()
