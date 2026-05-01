import uuid
from decimal import Decimal
from datetime import date


def parse_uuid_field(value, field_name: str, required: bool = True):
    if value is None or value == "":
        if required:
            return None, {"error": f"Missing {field_name}"}, 400
        return None, None, None

    if isinstance(value, uuid.UUID):
        return value, None, None

    if isinstance(value, str):
        try:
            return uuid.UUID(value), None, None
        except ValueError:
            return None, {"error": f"Invalid {field_name} format"}, 400

    return None, {"error": f"Invalid {field_name} type"}, 400


def validate_date_field(value, field_name: str, required: bool = True):
    if value is None or value == "":
        if required:
            return None, {"error": f"Missing {field_name}"}, 400
        return None, None, None

    try:
        parsed = date.fromisoformat(value)
        return parsed, None, None
    except ValueError:
        return None, {"error": f"Invalid {field_name} format, expected YYYY-MM-DD"}, 400


def validate_decimal_field(
    value,
    field_name: str,
    required: bool = True,
    min_value: Decimal | None = None,
    strictly_positive: bool = False,
):
    if value is None or value == "":
        if required:
            return None, {"error": f"Missing {field_name}"}, 400
        return None, None, None

    try:
        dec = Decimal(str(value))
    except Exception:
        return None, {"error": f"Invalid {field_name} format"}, 400

    if strictly_positive and dec <= 0:
        return None, {"error": f"{field_name} must be positive"}, 400

    if min_value is not None and dec < min_value:
        return None, {"error": f"{field_name} must be >= {min_value}"}, 400

    return dec, None, None


def validate_json_object(value, field_name: str, required: bool = False):
    if value is None:
        if required:
            return None, {"error": f"Missing {field_name}"}, 400
        return None, None, None

    if not isinstance(value, dict):
        return None, {"error": f"{field_name} must be JSON object"}, 400

    return value, None, None


def validate_json_body_object(payload, allow_empty: bool = True):
    if payload is None:
        return None, {"error": "Missing JSON body"}, 400

    if not isinstance(payload, dict):
        return None, {"error": "JSON body must be an object"}, 400

    if not allow_empty and not payload:
        return None, {"error": "Missing JSON body"}, 400

    return payload, None, None


def validate_required_string(value, field_name: str):
    text = (value or "").strip()
    if not text:
        return None, {"error": f"Missing {field_name}"}, 400
    return text, None, None


def validate_non_empty_string(value, field_name: str):
    if value is None:
        return None, None, None

    text = str(value).strip()
    if not text:
        return None, {"error": f"{field_name} cannot be empty"}, 400

    return text, None, None


def parse_optional_int_query_param(value, field_name: str):
    if value is None:
        return None, None, None

    try:
        return int(value), None, None
    except (TypeError, ValueError):
        return None, {"error": f"Invalid {field_name} format"}, 400


def parse_month_year_query_params(year_raw, month_raw):
    year, year_err, _ = parse_optional_int_query_param(year_raw, "year")
    if year_err:
        return None, None, {"error": "Invalid year/month format"}, 400

    month, month_err, _ = parse_optional_int_query_param(month_raw, "month")
    if month_err:
        return None, None, {"error": "Invalid year/month format"}, 400

    return year, month, None, None


def is_valid_calendar_year(year: int) -> bool:
    return 1 <= year <= 9999


def validate_month_year_filter(year: int | None, month: int | None):
    if (year is None) ^ (month is None):
        return None, None, {"error": "Both year and month must be provided together"}, 400

    if year is None and month is None:
        return None, None, None, None

    if not is_valid_calendar_year(year):
        return None, None, {"error": "Invalid year/month format"}, 400

    if month < 1 or month > 12:
        return None, None, {"error": "Month must be between 1 and 12"}, 400

    try:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    except ValueError:
        return None, None, {"error": "Invalid year/month format"}, 400

    return start, end, None, None
