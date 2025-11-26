"""Marshmallow schemas for the Receipt model and related API payloads."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from marshmallow import Schema, fields, post_load


class ReceiptCreateSchema(Schema):
    """Schema for creating a new receipt.

    Used for POST /api/receipts. All required fields must be provided.
    """

    user_id = fields.UUID(required=True)
    organization_id = fields.UUID(required=False, allow_none=True)
    merchant = fields.String(required=False, allow_none=True)

    issue_date = fields.Date(required=True)
    currency = fields.String(required=False, load_default="EUR")

    total_amount = fields.Decimal(required=True, as_string=True)
    external_uid = fields.String(required=False, allow_none=True)
    extra_metadata = fields.Dict(required=False, allow_none=True)

    @post_load
    def _normalize(self, data, **kwargs):
        # ensure Decimal
        if "total_amount" in data and isinstance(data["total_amount"], str):
            data["total_amount"] = Decimal(data["total_amount"])
        return data


class ReceiptUpdateSchema(Schema):
    """Schema for updating a receipt (PUT /api/receipts/{receipt_id})."""

    organization_id = fields.UUID(required=False, allow_none=True)
    merchant = fields.String(required=False, allow_none=True)

    issue_date = fields.Date(required=False)
    currency = fields.String(required=False)

    total_amount = fields.Decimal(required=False, as_string=True)
    external_uid = fields.String(required=False, allow_none=True)
    extra_metadata = fields.Dict(required=False, allow_none=True)

    @post_load
    def _normalize(self, data, **kwargs):
        if "total_amount" in data and isinstance(data["total_amount"], str):
            data["total_amount"] = Decimal(data["total_amount"])
        return data


class ReceiptSchema(Schema):
    """Full receipt representation (used in responses)."""

    id = fields.UUID(required=True)
    user_id = fields.UUID(required=True)
    organization_id = fields.UUID(allow_none=True)
    merchant = fields.String(allow_none=True)

    issue_date = fields.Date(required=True)
    currency = fields.String(required=True)

    total_amount = fields.Decimal(required=True, as_string=True)
    external_uid = fields.String(allow_none=True)
    extra_metadata = fields.Dict(allow_none=True)
    created_at = fields.DateTime(allow_none=True)


class ReceiptsListSchema(Schema):
    """List response schema for GET /api/receipts."""

    receipts = fields.List(fields.Nested(ReceiptSchema), required=True)
