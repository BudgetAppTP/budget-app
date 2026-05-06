from decimal import Decimal

from app.validators.common_validators import (
    parse_uuid_field,
    validate_decimal_field,
    validate_json_object,
    validate_non_empty_string,
    validate_required_string,
)


def validate_receipt_item_create_data(data: dict):
    name = validate_required_string(data.get("name"), "name")
    quantity = validate_decimal_field(
        data.get("quantity", 1),
        "quantity",
        required=True,
        min_value=Decimal("0.001"),
    )

    unit_price = validate_decimal_field(
        data.get("unit_price", 0),
        "unit_price",
        required=True,
        min_value=Decimal("0"),
    )

    extra_metadata = validate_json_object(data.get("extra_metadata"), "extra_metadata")
    category_id = parse_uuid_field(data.get("category_id"), "category_id", required=False)

    return {
        "name": name,
        "quantity": quantity,
        "unit_price": unit_price,
        "category_id": category_id,
        "extra_metadata": extra_metadata,
    }


def validate_receipt_item_update_data(data: dict):
    cleaned = {}

    if "name" in data:
        cleaned["name"] = validate_non_empty_string(data.get("name"), "name")

    if "quantity" in data:
        cleaned["quantity"] = validate_decimal_field(
            data.get("quantity"),
            "quantity",
            required=True,
            min_value=Decimal("0.001"),
        )

    if "unit_price" in data:
        cleaned["unit_price"] = validate_decimal_field(
            data.get("unit_price"),
            "unit_price",
            required=True,
            min_value=Decimal("0"),
        )

    if "category_id" in data:
        cleaned["category_id"] = parse_uuid_field(
            data.get("category_id"),
            "category_id",
            required=False,
        )

    if "extra_metadata" in data:
        cleaned["extra_metadata"] = validate_json_object(data.get("extra_metadata"), "extra_metadata")

    return cleaned
