"""
OpenAPI builder based on Marshmallow schemas + Apispec.

- Schemas in app/schemas/* are the single source of truth.
- This file generates Swagger/OpenAPI json into app/static/swagger.json
- Covered endpoints:
    * /api/incomes (GET, POST)
    * /api/incomes/{income_id} (GET, PUT, DELETE)
    * /api/receipts (GET, POST)
    * /api/receipts/{receipt_id} (GET, PUT, DELETE)

Other endpoints will still appear via the fallback swagger_auto generator.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from app.schemas import (
    IncomeSchema,
    IncomeCreateSchema,
    IncomeUpdateSchema,
    IncomesListSchema,
    ReceiptSchema,
    ReceiptCreateSchema,
    ReceiptUpdateSchema,
    ReceiptsListSchema,
)


def build_spec(app, title: str = "Budget API", version: str = "1.0.0") -> Dict[str, Any]:
    spec = APISpec(
      title=title,
      version=version,
      openapi_version="3.0.3",
      plugins=[MarshmallowPlugin()],
    )


    # Register schema components
    spec.components.schema("Income", schema=IncomeSchema)
    spec.components.schema("IncomeCreate", schema=IncomeCreateSchema)
    spec.components.schema("IncomeUpdate", schema=IncomeUpdateSchema)
    spec.components.schema("IncomesList", schema=IncomesListSchema)

    spec.components.schema("Receipt", schema=ReceiptSchema)
    spec.components.schema("ReceiptCreate", schema=ReceiptCreateSchema)
    spec.components.schema("ReceiptUpdate", schema=ReceiptUpdateSchema)
    spec.components.schema("ReceiptsList", schema=ReceiptsListSchema)

    # ---------- INCOMES ----------
    spec.path(
        path="/api/incomes",
        operations={
            "get": {
                "summary": "List incomes with optional sorting",
                "parameters": [
                    {
                        "in": "query",
                        "name": "sort",
                        "schema": {"type": "string", "enum": ["income_date", "amount"]},
                        "required": False,
                        "description": "Field to sort by",
                    },
                    {
                        "in": "query",
                        "name": "order",
                        "schema": {"type": "string", "enum": ["asc", "desc"]},
                        "required": False,
                        "description": "Sort order",
                    },
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/IncomesList"}
                            }
                        },
                    }
                },
            },
            "post": {
                "summary": "Create a new income entry",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/IncomeCreate"}
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Income created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "format": "uuid"},
                                        "message": {"type": "string"},
                                    },
                                    "required": ["id", "message"],
                                }
                            }
                        },
                    },
                    "400": {"description": "Invalid input data"},
                },
            },
        },
    )

    income_id_param = {
        "in": "path",
        "name": "income_id",
        "required": True,
        "schema": {"type": "string", "format": "uuid"},
        "description": "Income identifier",
    }

    spec.path(
        path="/api/incomes/{income_id}",
        operations={
            "get": {
                "summary": "Get income by ID",
                "parameters": [income_id_param],
                "responses": {
                    "200": {
                        "description": "Income found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Income"}
                            }
                        },
                    },
                    "404": {"description": "Income not found"},
                },
            },
            "put": {
                "summary": "Update income by ID",
                "parameters": [income_id_param],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/IncomeUpdate"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Income updated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "format": "uuid"},
                                        "message": {"type": "string"},
                                    },
                                    "required": ["id", "message"],
                                }
                            }
                        },
                    },
                    "400": {"description": "Invalid input"},
                    "404": {"description": "Income not found"},
                },
            },
            "delete": {
                "summary": "Delete income by ID",
                "parameters": [income_id_param],
                "responses": {
                    "200": {"description": "Income deleted"},
                    "404": {"description": "Income not found"},
                },
            },
        },
    )

    # ---------- RECEIPTS ----------
    spec.path(
        path="/api/receipts",
        operations={
            "get": {
                "summary": "List receipts",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ReceiptsList"}
                            }
                        },
                    }
                },
            },
            "post": {
                "summary": "Create a new receipt",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ReceiptCreate"}
                        }
                    },
                },
                "responses": {
                    "201": {
                        "description": "Receipt created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "format": "uuid"},
                                        "message": {"type": "string"},
                                    },
                                    "required": ["id", "message"],
                                }
                            }
                        },
                    },
                    "400": {"description": "Invalid input data"},
                },
            },
        },
    )

    receipt_id_param = {
        "in": "path",
        "name": "receipt_id",
        "required": True,
        "schema": {"type": "string", "format": "uuid"},
        "description": "Receipt identifier",
    }

    spec.path(
        path="/api/receipts/{receipt_id}",
        operations={
            "get": {
                "summary": "Get receipt by ID",
                "parameters": [receipt_id_param],
                "responses": {
                    "200": {
                        "description": "Receipt found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Receipt"}
                            }
                        },
                    },
                    "404": {"description": "Receipt not found"},
                },
            },
            "put": {
                "summary": "Update receipt by ID",
                "parameters": [receipt_id_param],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ReceiptUpdate"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Receipt updated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "format": "uuid"},
                                        "message": {"type": "string"},
                                    },
                                    "required": ["id", "message"],
                                }
                            }
                        },
                    },
                    "400": {"description": "Invalid input"},
                    "404": {"description": "Receipt not found"},
                },
            },
            "delete": {
                "summary": "Delete receipt by ID",
                "parameters": [receipt_id_param],
                "responses": {
                    "200": {"description": "Receipt deleted"},
                    "404": {"description": "Receipt not found"},
                },
            },
        },
    )

    return spec.to_dict()


def write_spec(app, out_path: str | None = None) -> str:
    spec_dict = build_spec(
        app,
        title=app.config.get("SWAGGER_TITLE", "Budget API"),
        version=app.config.get("SWAGGER_VERSION", "1.0.0"),
    )

    if out_path is None:
        out_path = str(Path(app.root_path) / "static" / "swagger.json")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec_dict, f, indent=2, ensure_ascii=False)

    return out_path
