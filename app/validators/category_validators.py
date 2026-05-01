from app.services.errors import BadRequestError
from app.validators.common_validators import parse_uuid_field, validate_decimal_field


def _validate_category_name_required(value):
    if value is None:
        raise BadRequestError("Missing name")

    text = str(value).strip()
    if not text:
        raise BadRequestError("Missing name")

    return text


def _validate_optional_parent_id(value):
    if value is None:
        return None

    if value == "":
        raise BadRequestError("Invalid input data")

    return parse_uuid_field(value, "parent_id", required=False)

def _validate_optional_limit(value):
    if value is None:
        return None

    if value == "":
        raise BadRequestError("Invalid input data")

    return validate_decimal_field(
        value,
        "limit",
        required=True,
    )


def validate_category_create_data(data: dict):
    name = _validate_category_name_required(data.get("name"))
    parent_id = _validate_optional_parent_id(data.get("parent_id"))
    limit = _validate_optional_limit(data.get("limit"))

    return {
        "name": name,
        "parent_id": parent_id,
        "limit": limit,
    }


def validate_category_update_data(data: dict):
    cleaned = {}

    if "name" in data:
        cleaned["name"] = _validate_category_name_required(data.get("name"))

    if "is_pinned" in data:
        cleaned["is_pinned"] = data["is_pinned"]

    if "count" in data:
        try:
            cleaned["count"] = int(data["count"])
        except (TypeError, ValueError):
            raise BadRequestError("Invalid input data")

    if "limit" in data:
        cleaned["limit"] = _validate_optional_limit(data.get("limit"))

    return cleaned
