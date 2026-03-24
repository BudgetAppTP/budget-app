import re

EMAIL_REGEX = r"^[^@]+@[^@]+\.[^@]+$"


def validate_user_create_data(data: dict):
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password_hash = data.get("password_hash")

    if not username:
        return None, {"error": "Missing username"}, 400

    if not email:
        return None, {"error": "Missing email"}, 400

    if not password_hash:
        return None, {"error": "Missing password_hash"}, 400

    if len(username) > 32:
        return None, {"error": "username must be at most 32 characters"}, 400

    if len(email) > 255:
        return None, {"error": "email must be at most 255 characters"}, 400

    if len(str(password_hash)) > 255:
        return None, {"error": "password_hash must be at most 255 characters"}, 400

    if not re.match(EMAIL_REGEX, email):
        return None, {"error": "Invalid email format"}, 400

    return {
        "username": username,
        "email": email,
        "password_hash": password_hash,
    }, None, None