from decimal import Decimal

from app.validators.common_validators import (
    parse_uuid_field,
    validate_date_field,
    validate_decimal_field,
    validate_json_object,
    validate_required_string,
    validate_non_empty_string,
)


def validate_receipt_create_data(data: dict):
    user_id = parse_uuid_field(data.get("user_id"), "user_id")
    description = validate_required_string(data.get("description"), "description")
    issue_date = validate_date_field(data.get("issue_date"), "issue_date", required=True)
    total_amount = validate_decimal_field(
        data.get("total_amount"),
        "total_amount",
        required=True,
        strictly_positive=True,
    )
    extra_metadata = validate_json_object(data.get("extra_metadata"), "extra_metadata")

    return {
        "user_id": user_id,
        "tag_id": data.get("tag_id"),
        "description": description,
        "issue_date": issue_date,
        "currency": data.get("currency", "EUR"),
        "total_amount": total_amount,
        "external_uid": data.get("external_uid"),
        "extra_metadata": extra_metadata,
    }


def validate_receipt_update_data(data: dict):
    cleaned = {}

    if "description" in data:
        cleaned["description"] = validate_non_empty_string(data.get("description"), "description")

    if "issue_date" in data:
        cleaned["issue_date"] = validate_date_field(data.get("issue_date"), "issue_date", required=True)

    if "total_amount" in data:
        cleaned["total_amount"] = validate_decimal_field(
            data.get("total_amount"),
            "total_amount",
            required=True,
            strictly_positive=True,
        )

    if "extra_metadata" in data:
        cleaned["extra_metadata"] = validate_json_object(data.get("extra_metadata"), "extra_metadata")

    if "currency" in data:
        cleaned["currency"] = data.get("currency")

    if "external_uid" in data:
        cleaned["external_uid"] = data.get("external_uid")

    if "tag_id" in data:
        cleaned["tag_id"] = data.get("tag_id")

    return cleaned
