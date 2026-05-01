from app.models.tag import TagType
from app.services.errors import BadRequestError
from app.validators.common_validators import (
    parse_uuid_field,
    validate_required_string,
    validate_non_empty_string,
)


def validate_tag_create_data(data: dict):
    user_id = parse_uuid_field(data.get("user_id"), "user_id")
    name = validate_required_string(data.get("name"), "name")

    tag_type = None
    if "type" in data and data.get("type") is not None:
        try:
            tag_type = TagType(data.get("type"))
        except ValueError:
            raise BadRequestError("Invalid tag type")

    return {
        "user_id": user_id,
        "name": name,
        "type": tag_type,
    }


def validate_tag_update_data(data: dict):
    cleaned = {}

    if "name" in data:
        cleaned["name"] = validate_non_empty_string(data.get("name"), "name")

    if "type" in data and data.get("type") is not None:
        try:
            cleaned["type"] = TagType(data.get("type"))
        except ValueError:
            raise BadRequestError("Invalid tag type")

    return cleaned
