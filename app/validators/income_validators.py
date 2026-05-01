from app.validators.common_validators import (
    validate_date_field,
    validate_decimal_field,
    validate_json_object,
    validate_required_string,
    validate_non_empty_string,
)


def validate_income_create_data(data: dict):
    description, err, status = validate_required_string(data.get("description"), "description")
    if err:
        return None, err, status

    amount, err, status = validate_decimal_field(
        data.get("amount"),
        "amount",
        required=True,
        strictly_positive=True,
    )
    if err:
        return None, err, status

    income_date, err, status = validate_date_field(
        data.get("income_date"),
        "income_date",
        required=True,
    )
    if err:
        return None, err, status

    extra_metadata, err, status = validate_json_object(
        data.get("extra_metadata"),
        "extra_metadata",
    )
    if err:
        return None, err, status

    return {
        "tag_id": data.get("tag_id"),
        "description": description,
        "amount": amount,
        "income_date": income_date,
        "extra_metadata": extra_metadata,
    }, None, None


def validate_income_update_data(data: dict):
    cleaned = {}

    if "description" in data:
        description, err, status = validate_non_empty_string(
            data.get("description"),
            "description",
        )
        if err:
            return None, err, status
        cleaned["description"] = description

    if "amount" in data:
        amount, err, status = validate_decimal_field(
            data.get("amount"),
            "amount",
            required=True,
            strictly_positive=True,
        )
        if err:
            return None, err, status
        cleaned["amount"] = amount

    if "income_date" in data:
        income_date, err, status = validate_date_field(
            data.get("income_date"),
            "income_date",
            required=True,
        )
        if err:
            return None, err, status
        cleaned["income_date"] = income_date

    if "extra_metadata" in data:
        extra_metadata, err, status = validate_json_object(
            data.get("extra_metadata"),
            "extra_metadata",
        )
        if err:
            return None, err, status
        cleaned["extra_metadata"] = extra_metadata

    if "tag_id" in data:
        cleaned["tag_id"] = data.get("tag_id")

    return cleaned, None, None
