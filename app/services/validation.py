from app.services.errors import BadRequestError
from app.validators.common_validators import validate_month_year_filter


def resolve_month_year_filter_or_raise(year: int | None, month: int | None):
    start, end, err, status = validate_month_year_filter(year, month)
    if err:
        raise BadRequestError(err["error"], status_code=status)
    return start, end
