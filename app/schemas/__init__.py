"""Marshmallow schemas for API requests and responses.

This package defines the Marshmallow schemas used to validate input and
serialize output for API endpoints.  By centralizing schemas here, the
application ensures a single source of truth for the API contract and
enables automatic Swagger/OpenAPI generation via Apispec.
"""

from .income import (
    IncomeSchema,
    IncomeCreateSchema,
    IncomeUpdateSchema,
    IncomesListSchema,
)
from .receipt import (
    ReceiptSchema,
    ReceiptCreateSchema,
    ReceiptUpdateSchema,
    ReceiptsListSchema,
)

__all__ = [
    "IncomeSchema",
    "IncomeCreateSchema",
    "IncomeUpdateSchema",
    "IncomesListSchema",
    "ReceiptSchema",
    "ReceiptCreateSchema",
    "ReceiptUpdateSchema",
    "ReceiptsListSchema",
]
