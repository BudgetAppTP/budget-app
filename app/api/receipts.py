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

from flask import request
from app.api import bp, make_response
from app.services import receipts_service


@bp.get("/receipts", strict_slashes=False)
def api_receipts_list():
    """
    GET /api/receipts/
    Summary: List receipts

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
    """
    receipts = receipts_service.get_all_receipts()
    return make_response(receipts, None, 200)


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
        "currency": "EUR",                 # optional, default: "EUR"
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
        "currency": "EUR",                 # optional
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

    # Basic validation of required fields
    if "receiptId" not in payload or "user_id" not in payload:
        return make_response(
            None,
            {"code": "bad_request", "message": "Missing receiptId or user_id"},
            400,
        )

    receipt_id = payload["receiptId"]
    user_id = payload["user_id"]

    service_payload, status = receipts_service.import_receipt_from_ekasa(
        receipt_id, user_id
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