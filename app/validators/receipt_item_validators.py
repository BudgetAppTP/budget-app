from decimal import Decimal

from app.validators.common_validators import (
    validate_decimal_field,
    validate_json_object,
    validate_required_string,
    validate_non_empty_string,
)


def validate_receipt_item_create_data(data: dict):
    name, err, status = validate_required_string(data.get("name"), "name")
    if err:
        return None, err, status

    quantity, err, status = validate_decimal_field(
        data.get("quantity", 1),
        "quantity",
        required=True,
        min_value=Decimal("0.001"),
    )
    if err:
        return None, err, status

    unit_price, err, status = validate_decimal_field(
        data.get("unit_price", 0),
        "unit_price",
        required=True,
        min_value=Decimal("0"),
    )
    if err:
        return None, err, status

    extra_metadata, err, status = validate_json_object(data.get("extra_metadata"), "extra_metadata")
    if err:
        return None, err, status

    return {
        "name": name,
        "quantity": quantity,
        "unit_price": unit_price,
        "category_id": data.get("category_id"),
        "extra_metadata": extra_metadata,
    }, None, None


def validate_receipt_item_update_data(data: dict):
    cleaned = {}

    if "name" in data:
        name, err, status = validate_non_empty_string(data.get("name"), "name")
        if err:
            return None, err, status
        cleaned["name"] = name

    if "quantity" in data:
        quantity, err, status = validate_decimal_field(
            data.get("quantity"),
            "quantity",
            required=True,
            min_value=Decimal("0.001"),
        )
        if err:
            return None, err, status
        cleaned["quantity"] = quantity

    if "unit_price" in data:
        unit_price, err, status = validate_decimal_field(
            data.get("unit_price"),
            "unit_price",
            required=True,
            min_value=Decimal("0"),
        )
        if err:
            return None, err, status
        cleaned["unit_price"] = unit_price

    if "category_id" in data:
        cleaned["category_id"] = data.get("category_id")

    if "extra_metadata" in data:
        extra_metadata, err, status = validate_json_object(data.get("extra_metadata"), "extra_metadata")
        if err:
            return None, err, status
        cleaned["extra_metadata"] = extra_metadata

    return cleaned, None, None