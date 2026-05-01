from app.validators.common_validators import (
    validate_date_field,
    validate_decimal_field,
    validate_json_object,
    validate_required_string,
    validate_non_empty_string,
)


def validate_income_create_data(data: dict):
    description = validate_required_string(data.get("description"), "description")
    amount = validate_decimal_field(
        data.get("amount"),
        "amount",
        required=True,
        strictly_positive=True,
    )

    income_date = validate_date_field(
        data.get("income_date"),
        "income_date",
        required=True,
    )

    extra_metadata = validate_json_object(
        data.get("extra_metadata"),
        "extra_metadata",
    )

    return {
        "tag_id": data.get("tag_id"),
        "description": description,
        "amount": amount,
        "income_date": income_date,
        "extra_metadata": extra_metadata,
    }


def validate_income_update_data(data: dict):
    cleaned = {}

    if "description" in data:
        cleaned["description"] = validate_non_empty_string(
            data.get("description"),
            "description",
        )

    if "amount" in data:
        cleaned["amount"] = validate_decimal_field(
            data.get("amount"),
            "amount",
            required=True,
            strictly_positive=True,
        )

    if "income_date" in data:
        cleaned["income_date"] = validate_date_field(
            data.get("income_date"),
            "income_date",
            required=True,
        )

    if "extra_metadata" in data:
        cleaned["extra_metadata"] = validate_json_object(
            data.get("extra_metadata"),
            "extra_metadata",
        )

    if "tag_id" in data:
        cleaned["tag_id"] = data.get("tag_id")

    return cleaned
