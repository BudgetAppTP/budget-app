"""
Receipts API

Paths:
  - GET    /api/receipts
  - GET    /api/receipts/tags
  - POST   /api/receipts
  - GET    /api/receipts/{receipt_id}
  - PUT    /api/receipts/{receipt_id}
  - DELETE /api/receipts/{receipt_id}
  - POST   /api/receipts/import-ekasa
  - GET    /api/receipts/ekasa-items

Response envelope:
  {"data": <payload> | null, "error": {"code": str, "message": str} | null}

Schemas:
  Receipt:
    {
      "id": uuid,
      "external_uid": "str | null",
      "tag": "str | null",
      "tag_id": "uuid | null",
      "description": str,
      "issue_date": "YYYY-MM-DD | null",
      "currency": "str | null",
      "total_amount": float,
      "extra_metadata": "object | null",
      "user_id": uuid,
      "account_id": uuid,
      "created_at": "ISO-8601 datetime | null"
    }

  ReceiptList:
    [Receipt]

  EkasaChecks:
    {
      "success": true,
      "checks": [object],
      "total_checks": int,
      "total_items": int
    }

Common errors:
  400: {"data": null, "error": {"code": "bad_request", "message": str}}
  403: {"data": null, "error": {"code": "forbidden", "message": str}}
  404: {"data": null, "error": {"code": "not_found", "message": str}}
  409: {"data": null, "error": {"code": "conflict", "message": str}}
"""

import uuid

from flask import g, request

from app.api import bp
from app.api.request_parsing import parse_json_object_body
from app.services import receipts_service, tags_service
from app.validators.common_validators import (
    parse_month_year_query_filter,
    parse_uuid_field,
)


@bp.get("/receipts", strict_slashes=False)
def api_receipts_list():
    """
    List receipts owned by the authenticated user.

    Query:
      sort: "issue_date" | "total_amount" (default: "issue_date")
      order: "asc" | "desc" (default: "desc")
      year: int | omitted
      month: int | omitted
      account_id: "uuid | omitted"

    Responses:
      200: {"data": ReceiptList, "error": null}
      400: see module errors
      403: see module errors
    """
    month_filter = parse_month_year_query_filter(
        request.args.get("year"),
        request.args.get("month"),
    )

    account_id = parse_uuid_field(
        request.args.get("account_id"),
        "account_id",
        required=False,
    )

    result = receipts_service.get_all_receipts(
        g.current_user.id,
        month_filter=month_filter,
        sort_by=request.args.get("sort", "issue_date"),
        descending=request.args.get("order", "desc").lower() == "desc",
        account_id=account_id,
    )
    return result.to_flask_response()


@bp.get("/receipts/tags", strict_slashes=False)
def api_expense_tags_list():
    """
    List expense-related tags for the authenticated user.

    Responses:
      200: {"data": {"success": true, "tags": [object]}, "error": null}
    """
    result = tags_service.get_expense_tags(user_id=g.current_user.id)
    return result.to_flask_response()


@bp.post("/receipts", strict_slashes=False)
def api_receipts_create():
    """
    Create a receipt for the authenticated user.

    Request:
      {
        "account_id": "uuid | omitted",
        "tag_id": "uuid | null | omitted",
        "description": str,
        "issue_date": "YYYY-MM-DD",
        "total_amount": float,
        "external_uid": "str | null | omitted",
        "extra_metadata": "object | null | omitted"
      }

    Responses:
      201: {"data": {"id": uuid, "message": str}, "error": null}
      400: see module errors
      403: see module errors
      404: see module errors
    """
    payload = parse_json_object_body()
    result = receipts_service.create_receipt(payload, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.get("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_get(receipt_id: uuid.UUID):
    """
    Get one receipt owned by the authenticated user.

    Path:
      receipt_id: uuid

    Responses:
      200: {"data": Receipt, "error": null}
      404: see module errors
    """
    result = receipts_service.get_receipt_by_id(receipt_id, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.put("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_update(receipt_id: uuid.UUID):
    """
    Update one receipt owned by the authenticated user.

    Path:
      receipt_id: uuid

    Request:
      {
        "tag_id": "uuid | null | omitted",
        "description": "str | omitted",
        "issue_date": "YYYY-MM-DD | omitted",
        "total_amount": "float | omitted",
        "external_uid": "str | null | omitted",
        "extra_metadata": "object | null | omitted"
      }

    Responses:
      200: {"data": {"id": uuid, "message": str}, "error": null}
      400: see module errors
      403: see module errors
      404: see module errors
    """
    payload = parse_json_object_body()
    result = receipts_service.update_receipt(
        receipt_id,
        payload,
        user_id=g.current_user.id,
    )
    return result.to_flask_response()


@bp.delete("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_delete(receipt_id: uuid.UUID):
    """
    Delete one receipt owned by the authenticated user.

    Path:
      receipt_id: uuid

    Responses:
      200: {"data": {"message": str}, "error": null}
      404: see module errors
    """
    result = receipts_service.delete_receipt(receipt_id, user_id=g.current_user.id)
    return result.to_flask_response()


@bp.post("/receipts/import-ekasa", strict_slashes=False)
def api_receipts_import_ekasa():
    """
    Import one eKasa receipt for the authenticated user.

    Request:
      {
        "receipt_id": str,
        "account_id": "uuid | omitted"
      }

    Responses:
      201: {"data": {"receipt_id": uuid, "message": str, "total_items": int}, "error": null}
      400: see module errors
      403: see module errors
      409: see module errors
    """
    payload = parse_json_object_body()
    result = receipts_service.import_receipt_from_ekasa(
        payload,
        user_id=g.current_user.id,
    )
    return result.to_flask_response()


@bp.get("/receipts/ekasa-items", strict_slashes=False)
def api_receipts_ekasa_items():
    """
    List eKasa-imported receipt items for the authenticated user.

    Query:
      year: int | omitted
      month: int | omitted
      account_id: "uuid | omitted"

    Responses:
      200: {"data": EkasaChecks, "error": null}
      400: see module errors
      403: see module errors
    """
    month_filter = parse_month_year_query_filter(
        request.args.get("year"),
        request.args.get("month"),
    )
    account_id = parse_uuid_field(
        request.args.get("account_id"),
        "account_id",
        required=False,
    )

    result = receipts_service.get_ekasa_items(
        month_filter=month_filter,
        user_id=g.current_user.id,
        account_id=account_id,
    )
    return result.to_flask_response()
