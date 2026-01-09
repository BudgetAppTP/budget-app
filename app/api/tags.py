"""
Tags API

Provides endpoints to manage tags and fetch tags filtered by type. These
endpoints follow the unified response contract of the API and wrap their
payloads in a common envelope via ``make_response``.

Paths:
  - GET    /api/tags/income    (list all income tags)
  - GET    /api/tags/expense   (list all expense tags)
  - POST   /api/tags           (create a new tag)
  - PUT    /api/tags/{id}      (update tag)
  - DELETE /api/tags/{id}      (delete tag)

Request/Response examples are documented inline with each view function.
"""

from __future__ import annotations

import uuid
from flask import request
from app.api import bp, make_response
from app.services import tags_service
from app.models.tag import TagType


@bp.get("/tags/income", strict_slashes=False)
def api_tags_income_list():
    """
    GET /api/tags/income
    Summary: List all income tags

    Responses:
      200:
        data: {"tags":[{...}], "count": number}
        error: null
      400:
        data: {"error": "Invalid tag type"}
        error: null
    """
    data, status = tags_service.get_tags_by_type(TagType.INCOME)
    if "error" in data:
        return make_response(data, None, status)
    return make_response(data, None, status)


@bp.get("/tags/expense", strict_slashes=False)
def api_tags_expense_list():
    """
    GET /api/tags/expense
    Summary: List all expense tags

    Responses are similar to /api/tags/income.
    """
    data, status = tags_service.get_tags_by_type(TagType.EXPENSE)
    if "error" in data:
        return make_response(data, None, status)
    return make_response(data, None, status)


@bp.post("/tags", strict_slashes=False)
def api_tags_create():
    """
    POST /api/tags
    Summary: Create a new tag

    Request (JSON example):
      {
        "user_id": "<uuid>",      # required
        "name": "Salary",        # required
        "type": "income"         # optional, one of income|expense|both
      }

    Responses:
      201:
        data: {"id": "<uuid>", "message": "Tag created successfully"}
        error: null
      400:
        data: {"error": "..."}
        error: null
    """
    payload = request.get_json(force=True) or {}
    data, status = tags_service.create_tag(payload)
    return make_response(data if "error" not in data else None, None if "error" not in data else data, status)


@bp.put("/tags/<uuid:tag_id>", strict_slashes=False)
def api_tags_update(tag_id: uuid.UUID):
    """
    PUT /api/tags/{tag_id}
    Summary: Update an existing tag

    Path:
      tag_id: uuid

    Request (JSON example):
      {
        "name": "Freelance",     # optional, if present must be non-empty
        "type": "expense"        # optional, one of income|expense|both
      }

    Responses:
      200:
        data: {"id": "<uuid>", "message": "Tag updated successfully"}
        error: null
      400/404:
        data: {"error": "..."}
        error: null
    """
    payload = request.get_json() or {}
    data, status = tags_service.update_tag(tag_id, payload)
    # errors come in data['error']; unify envelope accordingly
    if "error" in data:
        return make_response(None, {"code": "bad_request" if status == 400 else str(status), "message": data["error"]}, status)
    return make_response(data, None, status)


@bp.delete("/tags/<uuid:tag_id>", strict_slashes=False)
def api_tags_delete(tag_id: uuid.UUID):
    """
    DELETE /api/tags/{tag_id}
    Summary: Delete a tag

    Path:
      tag_id: uuid

    Responses:
      200:
        data: {"message": "Tag deleted successfully"}
        error: null
      400/404:
        data: {"error": "..."}
        error: null
    """
    data, status = tags_service.delete_tag(tag_id)
    if "error" in data:
        return make_response(None, {"code": "bad_request" if status == 400 else str(status), "message": data["error"]}, status)
    return make_response(data, None, status)
