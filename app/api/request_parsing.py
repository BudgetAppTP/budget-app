from flask import request

from app.validators.common_validators import validate_json_body_object


def parse_json_object_body(*, allow_empty: bool = True):
    return validate_json_body_object(
        request.get_json(silent=True),
        allow_empty=allow_empty,
    )
