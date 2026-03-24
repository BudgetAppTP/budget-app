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
    user_id, err, status = parse_uuid_field(data.get("user_id"), "user_id")
    if err:
        return None, err, status

    description, err, status = validate_required_string(data.get("description"), "description")
    if err:
        return None, err, status

    issue_date, err, status = validate_date_field(data.get("issue_date"), "issue_date", required=True)
    if err:
        return None, err, status

    total_amount, err, status = validate_decimal_field(
        data.get("total_amount"),
        "total_amount",
        required=True,
        strictly_positive=True,
    )
    if err:
        return None, err, status

    extra_metadata, err, status = validate_json_object(data.get("extra_metadata"), "extra_metadata")
    if err:
        return None, err, status

    return {
        "user_id": user_id,
        "tag_id": data.get("tag_id"),
        "description": description,
        "issue_date": issue_date,
        "currency": data.get("currency", "EUR"),
        "total_amount": total_amount,
        "external_uid": data.get("external_uid"),
        "extra_metadata": extra_metadata,
    }, None, None


def validate_receipt_update_data(data: dict):
    cleaned = {}

    if "description" in data:
        description, err, status = validate_non_empty_string(data.get("description"), "description")
        if err:
            return None, err, status
        cleaned["description"] = description

    if "issue_date" in data:
        issue_date, err, status = validate_date_field(data.get("issue_date"), "issue_date", required=True)
        if err:
            return None, err, status
        cleaned["issue_date"] = issue_date

    if "total_amount" in data:
        total_amount, err, status = validate_decimal_field(
            data.get("total_amount"),
            "total_amount",
            required=True,
            strictly_positive=True,
        )
        if err:
            return None, err, status
        cleaned["total_amount"] = total_amount

    if "extra_metadata" in data:
        extra_metadata, err, status = validate_json_object(data.get("extra_metadata"), "extra_metadata")
        if err:
            return None, err, status
        cleaned["extra_metadata"] = extra_metadata

    if "currency" in data:
        cleaned["currency"] = data.get("currency")

    if "external_uid" in data:
        cleaned["external_uid"] = data.get("external_uid")

    if "tag_id" in data:
        cleaned["tag_id"] = data.get("tag_id")

    return cleaned, None, None