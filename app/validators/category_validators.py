from app.validators.common_validators import parse_uuid_field, validate_decimal_field


def _invalid_input_error():
    return {"error": "Invalid input data"}, 400


def _validate_category_name_required(value):
    if value is None:
        return None, {"error": "Missing name"}, 400

    text = str(value).strip()
    if not text:
        return None, {"error": "Missing name"}, 400

    return text, None, None


def _validate_optional_parent_id(value):
    if value is None:
        return None, None, None

    if value == "":
        return None, *_invalid_input_error()

    parent_id, err, status = parse_uuid_field(value, "parent_id", required=False)
    if err:
        return None, *_invalid_input_error()

    return parent_id, None, None


def _validate_optional_limit(value):
    if value is None:
        return None, None, None

    if value == "":
        return None, *_invalid_input_error()

    limit, err, status = validate_decimal_field(
        value,
        "limit",
        required=True,
    )
    if err:
        return None, *_invalid_input_error()

    return limit, None, None


def validate_category_create_data(data: dict):
    name, err, status = _validate_category_name_required(data.get("name"))
    if err:
        return None, err, status

    parent_id, err, status = _validate_optional_parent_id(data.get("parent_id"))
    if err:
        return None, err, status

    limit, err, status = _validate_optional_limit(data.get("limit"))
    if err:
        return None, err, status

    return {
        "name": name,
        "parent_id": parent_id,
        "limit": limit,
    }, None, None


def validate_category_update_data(data: dict):
    cleaned = {}

    if "name" in data:
        name, err, status = _validate_category_name_required(data.get("name"))
        if err:
            return None, err, status
        cleaned["name"] = name

    if "is_pinned" in data:
        cleaned["is_pinned"] = data["is_pinned"]

    if "count" in data:
        try:
            cleaned["count"] = int(data["count"])
        except (TypeError, ValueError):
            return None, *_invalid_input_error()

    if "limit" in data:
        limit, err, status = _validate_optional_limit(data.get("limit"))
        if err:
            return None, err, status
        cleaned["limit"] = limit

    return cleaned, None, None
