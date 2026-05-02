import uuid
from dataclasses import dataclass
from decimal import Decimal
from datetime import date

from app.services.errors import BadRequestError


def parse_uuid_field(value, field_name: str, required: bool = True):
    if value is None or value == "":
        if required:
            raise BadRequestError(f"Missing {field_name}")
        return None

    if isinstance(value, uuid.UUID):
        return value

    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            raise BadRequestError(f"Invalid {field_name} format")

    raise BadRequestError(f"Invalid {field_name} type")


def validate_date_field(value, field_name: str, required: bool = True):
    if value is None or value == "":
        if required:
            raise BadRequestError(f"Missing {field_name}")
        return None

    try:
        parsed = date.fromisoformat(value)
        return parsed
    except ValueError:
        raise BadRequestError(f"Invalid {field_name} format, expected YYYY-MM-DD")


def validate_decimal_field(
    value,
    field_name: str,
    required: bool = True,
    min_value: Decimal | None = None,
    strictly_positive: bool = False,
):
    if value is None or value == "":
        if required:
            raise BadRequestError(f"Missing {field_name}")
        return None

    try:
        dec = Decimal(str(value))
    except Exception:
        raise BadRequestError(f"Invalid {field_name} format")

    if strictly_positive and dec <= 0:
        raise BadRequestError(f"{field_name} must be positive")

    if min_value is not None and dec < min_value:
        raise BadRequestError(f"{field_name} must be >= {min_value}")

    return dec


def validate_json_object(value, field_name: str, required: bool = False):
    if value is None:
        if required:
            raise BadRequestError(f"Missing {field_name}")
        return None

    if not isinstance(value, dict):
        raise BadRequestError(f"{field_name} must be JSON object")

    return value


def validate_json_body_object(payload, allow_empty: bool = True):
    if payload is None:
        raise BadRequestError("Missing JSON body")

    if not isinstance(payload, dict):
        raise BadRequestError("JSON body must be an object")

    if not allow_empty and not payload:
        raise BadRequestError("Missing JSON body")

    return payload


def validate_required_string(value, field_name: str):
    text = (value or "").strip()
    if not text:
        raise BadRequestError(f"Missing {field_name}")
    return text


def validate_non_empty_string(value, field_name: str):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        raise BadRequestError(f"{field_name} cannot be empty")

    return text


@dataclass(frozen=True)
class MonthYearFilter:
    year: int | None
    month: int | None
    start: date | None
    end: date | None

    def range(self) -> tuple[date | None, date | None]:
        return self.start, self.end


def parse_month_year_query_filter(year_raw, month_raw) -> MonthYearFilter:
    if year_raw is None:
        year = None
    else:
        try:
            year = int(year_raw)
        except (TypeError, ValueError) as exc:
            raise BadRequestError("Invalid year format") from exc

    if month_raw is None:
        month = None
    else:
        try:
            month = int(month_raw)
        except (TypeError, ValueError) as exc:
            raise BadRequestError("Invalid month format") from exc

    return validate_month_year_filter(year, month)


def validate_month_year_filter(year: int | None, month: int | None) -> MonthYearFilter:
    if (year is None) ^ (month is None):
        raise BadRequestError("Both year and month must be provided together")

    if year is None and month is None:
        return MonthYearFilter(year=None, month=None, start=None, end=None)

    if not 1 <= year <= 9999:
        raise BadRequestError("Invalid year format")

    if month < 1 or month > 12:
        raise BadRequestError("Month must be between 1 and 12")

    try:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    except ValueError:
        raise BadRequestError("Invalid year/month format")

    return MonthYearFilter(year=year, month=month, start=start, end=end)
