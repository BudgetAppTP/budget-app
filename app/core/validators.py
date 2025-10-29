from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
from .domain import Section, TransactionKind


def parse_date_ymd(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_month_ym(value: str):
    datetime.strptime(value, "%Y-%m")
    return value


def parse_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        d = value
    else:
        d = Decimal(str(value))
    return d.quantize(Decimal("0.01"))


def ensure_non_negative(d: Decimal) -> Decimal:
    if d < 0:
        raise ValueError("negative")
    return d


def validate_section(value: Optional[str]) -> Optional[Section]:
    if value is None:
        return None
    return Section(value)


def validate_kind(value: Optional[str]) -> Optional[TransactionKind]:
    if value is None:
        return None
    return TransactionKind(value)


def try_decimal(value) -> Optional[Decimal]:
    try:
        return parse_decimal(value)
    except (InvalidOperation, ValueError):
        return None
