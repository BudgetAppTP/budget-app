import re

from app.services.errors import BadRequestError

EMAIL_REGEX = r"^[^@]+@[^@]+\.[^@]+$"


def validate_user_create_data(data: dict):
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password_hash = data.get("password_hash")

    if not username:
        raise BadRequestError("Missing username")

    if not email:
        raise BadRequestError("Missing email")

    if not password_hash:
        raise BadRequestError("Missing password_hash")

    if len(username) > 32:
        raise BadRequestError("username must be at most 32 characters")

    if len(email) > 255:
        raise BadRequestError("email must be at most 255 characters")

    if len(str(password_hash)) > 255:
        raise BadRequestError("password_hash must be at most 255 characters")

    if not re.match(EMAIL_REGEX, email):
        raise BadRequestError("Invalid email format")

    return {
        "username": username,
        "email": email,
        "password_hash": password_hash,
    }
