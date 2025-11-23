"""Marshmallow schemas for the Income model and related API payloads."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from marshmallow import Schema, fields, post_load


class IncomeCreateSchema(Schema):
    """Schema for creating a new income.

    This schema validates incoming JSON for the POST /api/incomes endpoint.
    All required fields must be present, and optional fields may be null.
    """

    user_id = fields.UUID(required=True, data_key="user_id")
    organization_id = fields.UUID(allow_none=True, data_key="organization_id")
    amount = fields.Decimal(as_string=True, required=True, data_key="amount")
    income_date = fields.Date(required=True, data_key="income_date")
    source = fields.String(allow_none=True)
    extra_metadata = fields.Dict(allow_none=True)

    @post_load
    def _cast_amount(self, data: dict, **kwargs) -> dict:
        """Convert amount to Decimal for use in the service layer."""
        value = data.get("amount")
        if value is not None and not isinstance(value, Decimal):
            data["amount"] = Decimal(str(value))
        return data


class IncomeUpdateSchema(Schema):
    """Schema for updating an existing income.

    All fields are optional; only those provided will be updated.
    """

    amount = fields.Decimal(as_string=True, required=False)
    income_date = fields.Date(required=False)
    organization_id = fields.UUID(allow_none=True, required=False)
    source = fields.String(allow_none=True, required=False)
    extra_metadata = fields.Dict(allow_none=True, required=False)

    @post_load
    def _cast_amount(self, data: dict, **kwargs) -> dict:
        value = data.get("amount")
        if value is not None and not isinstance(value, Decimal):
            data["amount"] = Decimal(str(value))
        return data


class IncomeSchema(Schema):
    """Schema representing a single income record in responses."""

    id = fields.UUID(required=True)
    user_id = fields.UUID(required=True)
    organization_id = fields.UUID(allow_none=True)
    amount = fields.Decimal(as_string=True, required=True)
    income_date = fields.Date(required=True)
    source = fields.String(allow_none=True)
    extra_metadata = fields.Dict(allow_none=True)


class IncomesListSchema(Schema):
    """Schema representing a list of incomes along with a total."""

    success = fields.Boolean(required=True)
    incomes = fields.List(fields.Nested(IncomeSchema), required=True)
    total_amount = fields.Decimal(as_string=True, required=True)
