"""
Receipts API

Paths:
  - GET    /api/receipts/                 List receipts
  - POST   /api/receipts/                 Create receipt
  - GET    /api/receipts/{receipt_id}     Get receipt by id
  - PUT    /api/receipts/{receipt_id}     Update receipt
  - DELETE /api/receipts/{receipt_id}     Delete receipt

Notes:
- Swagger может показывать «сырой» JSON (без конверта). Фактический ответ — в конверте:
  { "data": <payload>, "error": null }.
"""
import uuid

from flask import request
from app.api import bp, make_response
from app.services import receipts_service, tags_service


@bp.get("/receipts", strict_slashes=False)
def api_receipts_list():
    """
    GET /api/receipts/
    Summary: List receipts with optional sorting and optional month/year filter

    Query:
      - sort: "issue_date" | "total_amount" (default: "issue_date")
      - order: "asc" | "desc" (default: "desc")
      - year: YYYY (optional, must be provided вместе с month)
      - month: 1..12 (optional, must be provided вместе с year)

    Notes:
      - If year+month are provided, endpoint returns only receipts from that month/year.

    Responses:
      200:
        data: [
          {
            "id": "<uuid>",
            "external_uid": "<str|null>",
            "tag": "Groceries" | null,
            "tag_id": "<uuid>" | null,
            "description": "Tesco groceries",
            "issue_date": "YYYY-MM-DD" | null,
            "currency": "EUR",
            "total_amount": number,
            "extra_metadata": { ... } | null,
            "user_id": "<uuid>",
            "created_at": "YYYY-MM-DDTHH:MM:SS+ZZ:ZZ" | null
          },
          ...
        ]
        error: null

      400:
        - If query params are invalid:
          data:
            { "error": "Both year and month must be provided together"
              | "Month must be between 1 and 12"
              | "Invalid year/month format"
            }
          error: null
    """
    sort_by = request.args.get("sort", "issue_date")
    order = request.args.get("order", "desc")
    reverse = order.lower() == "desc"

    year_raw = request.args.get("year")
    month_raw = request.args.get("month")
    account_raw = request.args.get("account_id")

    year = None
    month = None
    account_id = None

    # Parse year/month if provided
    try:
        if year_raw is not None:
            year = int(year_raw)
        if month_raw is not None:
            month = int(month_raw)
    except ValueError:
        return make_response({"error": "Invalid year/month format"}, None, 400)

    if account_raw:
        try:
            account_id = uuid.UUID(account_raw)
        except ValueError:
            return make_response({"error": "Invalid account_id format"}, None, 400)

    data, status = receipts_service.get_all_receipts(year=year, month=month, account_id=account_id)
    if status != 200:
        return make_response(data, None, status)
    try:
        data.sort(key=lambda r: r.get(sort_by), reverse=reverse)
    except Exception:
        pass

    return make_response(data, None, 200)


@bp.get("/receipts/tags", strict_slashes=False)
def api_expense_tags_list():
    """
    GET /api/receipts/tags
    Summary: Get all expense-related tags (type=EXPENSE or BOTH)

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
                "name": "Groceries",
                "type": "EXPENSE" | "BOTH",
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

    data, status = tags_service.get_expense_tags(user_id=user_id)
    return make_response(data, None, status)


@bp.post("/receipts", strict_slashes=False)
def api_receipts_create():
    """
    POST /api/receipts/
    Summary: Create receipt

    Request (JSON):
      {
        "user_id": "<uuid>",               # required
        "issue_date": "YYYY-MM-DD",        # optional (can be null/omitted)
        "description": "Tesco groceries",  # required, non-empty string
        "total_amount": 23.45,             # optional, default: 0.0
        "tag_id": "<uuid>",                # optional, must belong to the same user
        "external_uid": "<str>",           # optional, external receipt id
        "extra_metadata": { ... }          # optional JSON
      }

    Responses:
      201:
        data:
          {
            "id": "<uuid>",
            "message": "Receipt created successfully"
          }
        error: null

      400:
        - If body is missing:
          data: null
          error: {"code":"bad_request","message":"Missing JSON body"}

        - If validation fails (e.g. missing description, bad user/tag):
          data:
            {
              "error": "Missing user_id"
                | "Invalid user_id format"
                | "Invalid tag_id format"
                | "Tag not found"
                | "Tag does not belong to this user"
                | "Missing description"
                | "Invalid issue_date format, expected YYYY-MM-DD"
            }
          error: null
    """
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipts_service.create_receipt(payload)
    return make_response(response, None, status)


@bp.get("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_get(receipt_id):
    """
    GET /api/receipts/{receipt_id}
    Summary: Get receipt by id

    Path:
      receipt_id: uuid

    Responses:
      200:
        data:
          {
            "id": "<uuid>",
            "external_uid": "<str|null>",
            "tag": "Groceries" | null,
            "tag_id": "<uuid>" | null,
            "description": "Tesco groceries",
            "issue_date": "YYYY-MM-DD" | null,
            "currency": "EUR",
            "total_amount": number,
            "extra_metadata": { ... } | null,
            "user_id": "<uuid>",
            "created_at": "YYYY-MM-DDTHH:MM:SS+ZZ:ZZ" | null
          }
        error: null

      404:
        data:
          {
            "error": "Receipt not found"
          }
        error: null
    """
    receipt, status = receipts_service.get_receipt_by_id(receipt_id)
    return make_response(receipt, None, status)


@bp.put("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_update(receipt_id):
    """
    PUT /api/receipts/{receipt_id}
    Summary: Update receipt

    Path:
      receipt_id: uuid

    Request (JSON):
      {
        "issue_date": "YYYY-MM-DD",        # optional
        "description": "Updated text",     # optional, if present must be non-empty
        "total_amount": 25.00,             # optional
        "tag_id": "<uuid>",                # optional, null to detach tag
        "external_uid": "<str>",           # optional
        "extra_metadata": { ... }          # optional
      }

    Responses:
      200:
        data:
          {
            "id": "<uuid>",
            "message": "Receipt updated successfully"
          }
        error: null

      400:
        - If body is missing:
          data: null
          error: {"code":"bad_request","message":"Missing JSON body"}

        - If validation fails (e.g. empty description, invalid tag/date):
          data:
            {
              "error": "Description cannot be empty"
                | "Invalid tag_id format"
                | "Tag not found"
                | "Tag does not belong to this user"
                | "Invalid issue_date format, expected YYYY-MM-DD"
            }
          error: null

      404:
        data:
          {
            "error": "Receipt not found"
          }
        error: null
    """
    payload = request.get_json() or {}
    if not payload:
        return make_response(None, {"code": "bad_request", "message": "Missing JSON body"}, 400)
    response, status = receipts_service.update_receipt(receipt_id, payload)
    return make_response(response, None, status)


@bp.delete("/receipts/<uuid:receipt_id>", strict_slashes=False)
def api_receipts_delete(receipt_id):
    """
    DELETE /api/receipts/{receipt_id}
    Summary: Delete receipt

    Path:
      receipt_id: uuid

    Responses:
      200:
        data:
          {
            "message": "Receipt deleted successfully"
          }
        error: null

      404:
        data:
          {
            "error": "Receipt not found"
          }
        error: null
    """
    response, status = receipts_service.delete_receipt(receipt_id)
    return make_response(response, None, status)

@bp.post("/receipts/import-ekasa", strict_slashes=False)
def api_receipts_import_ekasa():
    """
    POST /api/receipts/import-ekasa
    Summary: Import receipt from eKasa

    Request (JSON):
      {
        "receiptId": "<string>",   # eKasa receiptId
        "user_id": "<uuid>"        # owner of the receipt (must exist)
      }

    Responses:
      201:
        data:
          {
            "message": "Receipt imported successfully",
            "tag": "Merchant name" | null,
            "tag_id": "<uuid>" | null,
            "receipt_id": "<uuid>",
            "total_items": 5
          }
        error: null

      400 / 4xx:
        - If required fields are missing:
          data: null
          error: {
            "code": "bad_request",
            "message": "Missing receiptId or user_id"
          }

        - If eKasa or import fails:
          data: null
          error: {
            "code": "ekasa_error",
            "message": "Import failed: ...",
            "details": {
              "error": "...",      # original error payload from service
              ...
            }
          }
    """
    payload = request.get_json() or {}

    receipt_id = payload.get("receiptId") or payload.get("receipt_id")
    user_id = payload.get("user_id") or payload.get("userId")
    account_id = payload.get("account_id") or payload.get("accountId")

    # Basic validation of required fields
    if not receipt_id or not user_id:
        return make_response(
            None,
            {"code": "bad_request", "message": "Missing receiptId or user_id"},
            400,
        )

    service_payload, status = receipts_service.import_receipt_from_ekasa(
        receipt_id, user_id, account_id
    )

    # receipts_service.import_receipt_from_ekasa returns (payload, status)
    # On error it returns {"error": "..."} – we map that into the `error` field.
    if status >= 400:
        if isinstance(service_payload, dict):
            msg = service_payload.get("error") or "Import from eKasa failed"
            details = service_payload
        else:
            msg = str(service_payload)
            details = None

        error_body = {"code": "ekasa_error", "message": msg}
        if details is not None:
            error_body["details"] = details

        return make_response(None, error_body, status)

    # Success path – payload goes into `data`
    return make_response(service_payload, None, status)


@bp.get("/receipts/ekasa-items", strict_slashes=False)
def api_receipts_ekasa_items():
    """
    GET /api/receipts/ekasa-items
    Summary: Get all eKasa items for a specific month+year, grouped by receipt (check)

    Query:
      - year: YYYY (required together with month)
      - month: 1..12 (required together with year)
      - user_id: uuid (optional filter)

    Notes:
      - Only receipts imported from eKasa are returned.
        (Detected by Receipt.external_uid != null)

    Responses:
      200:
        data:
          {
            "success": true,
            "checks": [
              {
                "receipt_id": "<uuid>",
                "external_uid": "<ekasa receiptId>",
                "issue_date": "YYYY-MM-DD",
                "description": "...",
                "currency": "EUR",
                "total_amount": number,
                "tag": "Groceries"|null,
                "tag_id": "<uuid>"|null,
                "user_id": "<uuid>",
                "items": [
                  {
                    "id": "<uuid>",
                    "name": "...",
                    "quantity": number,
                    "unit_price": number,
                    "total_price": number,
                    "category_id": "<uuid>"|null,
                    "extra_metadata": {...}|null
                  }
                ]
              }
            ],
            "total_checks": number,
            "total_items": number
          }
        error: null

      400:
        data: { "error": "Both year and month must be provided together"
                     | "Invalid year/month format"
                     | "Month must be between 1 and 12"
                     | "Invalid user_id format" }
        error: null
    """
    year_raw = request.args.get("year")
    month_raw = request.args.get("month")

    # optional user filter
    raw_user_id = request.args.get("user_id")
    raw_account_id = request.args.get("account_id")
    user_id = None
    account_id = None
    if raw_user_id:
        try:
            user_id = uuid.UUID(raw_user_id)
        except ValueError:
            return make_response({"error": "Invalid user_id format"}, None, 400)
    if raw_account_id:
        try:
            account_id = uuid.UUID(raw_account_id)
        except ValueError:
            return make_response({"error": "Invalid account_id format"}, None, 400)

    # Parse year/month (both optional, но должны быть вместе)
    year = None
    month = None
    try:
        if year_raw is not None:
            year = int(year_raw)
        if month_raw is not None:
            month = int(month_raw)
    except ValueError:
        return make_response({"error": "Invalid year/month format"}, None, 400)

    data, status = receipts_service.get_ekasa_items(
        year=year,
        month=month,
        user_id=user_id,
        account_id=account_id,
    )
    return make_response(data, None, status)
