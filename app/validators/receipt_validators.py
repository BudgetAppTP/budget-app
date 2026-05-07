from app.validators.common_validators import (
    parse_uuid_field,
    validate_date_field,
    validate_decimal_field,
    validate_json_object,
    validate_required_string,
    validate_non_empty_string,
)


def validate_receipt_create_data(data: dict):
    description = validate_required_string(data.get("description"), "description")
    issue_date = validate_date_field(data.get("issue_date"), "issue_date", required=True)
    total_amount = validate_decimal_field(
        data.get("total_amount"),
        "total_amount",
        required=True,
        strictly_positive=True,
    )
    tag_id = parse_uuid_field(
        data.get("tag_id"),
        "tag_id",
        required=False,
    )
    account_id = parse_uuid_field(
        data.get("account_id"),
        "account_id",
        required=False,
    )
    extra_metadata = validate_json_object(data.get("extra_metadata"), "extra_metadata")
    external_uid = data.get("external_uid")
    if external_uid is not None:
        external_uid = str(external_uid).strip() or None

    return {
        "tag_id": tag_id,
        "account_id": account_id,
        "description": description,
        "issue_date": issue_date,
        "total_amount": total_amount,
        "external_uid": external_uid,
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

    if "external_uid" in data:
        raw_external_uid = data.get("external_uid")
        cleaned["external_uid"] = None if raw_external_uid is None else str(raw_external_uid).strip() or None

    if "tag_id" in data:
        cleaned["tag_id"] = parse_uuid_field(
            data.get("tag_id"),
            "tag_id",
            required=False,
        )

    return cleaned
