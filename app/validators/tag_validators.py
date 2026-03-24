from app.models.tag import TagType
from app.validators.common_validators import (
    parse_uuid_field,
    validate_required_string,
    validate_non_empty_string,
)


def validate_tag_create_data(data: dict):
    user_id, err, status = parse_uuid_field(data.get("user_id"), "user_id")
    if err:
        return None, err, status

    name, err, status = validate_required_string(data.get("name"), "name")
    if err:
        return None, err, status

    tag_type = None
    if "type" in data and data.get("type") is not None:
        try:
            tag_type = TagType(data.get("type"))
        except ValueError:
            return None, {"error": "Invalid tag type"}, 400

    return {
        "user_id": user_id,
        "name": name,
        "type": tag_type,
    }, None, None


def validate_tag_update_data(data: dict):
    cleaned = {}

    if "name" in data:
        name, err, status = validate_non_empty_string(data.get("name"), "name")
        if err:
            return None, err, status
        cleaned["name"] = name

    if "type" in data and data.get("type") is not None:
        try:
            cleaned["type"] = TagType(data.get("type"))
        except ValueError:
            return None, {"error": "Invalid tag type"}, 400

    return cleaned, None, None