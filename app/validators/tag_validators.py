from app.models.tag import TagType
from app.services.errors import BadRequestError
from app.validators.common_validators import (
    validate_required_string,
    validate_non_empty_string,
)


def validate_tag_create_data(data: dict):
    name = validate_required_string(data.get("name"), "name")

    tag_type = TagType.BOTH
    if "type" in data and data.get("type") is not None:
        try:
            tag_type = TagType(data.get("type"))
        except ValueError:
            raise BadRequestError("Invalid tag type")

    return {
        "name": name,
        "type": tag_type,
    }


def validate_tag_update_data(data: dict):
    cleaned = {}

    if "name" in data:
        cleaned["name"] = validate_non_empty_string(data.get("name"), "name")

    if "type" in data:
        if data.get("type") is None:
            cleaned["type"] = None
        else:
            try:
                cleaned["type"] = TagType(data.get("type"))
            except ValueError:
                raise BadRequestError("Invalid tag type")

    return cleaned
