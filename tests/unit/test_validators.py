from decimal import Decimal

import pytest

from app.core.validators import ensure_non_negative, parse_decimal, parse_month_ym, try_decimal


def test_parse_decimal_quantizes_to_cents():
    assert parse_decimal("10.235") == Decimal("10.24")


def test_try_decimal_returns_none_for_invalid_input():
    assert try_decimal("not-a-number") is None


def test_ensure_non_negative_rejects_negative_values():
    with pytest.raises(ValueError, match="negative"):
        ensure_non_negative(Decimal("-0.01"))


def test_parse_month_ym_rejects_invalid_month():
    with pytest.raises(ValueError):
        parse_month_ym("2025-13")
