"""
Dashboard API

Path:
  - GET /api/dashboard?month=YYYY-MM

Returns summary cards for the given month and 6-month trend series.
"""

from datetime import date
from decimal import Decimal
from flask import current_app, request
from app.api import bp, make_response
from app.core.domain import TransactionKind
from app.core.dto import TransactionFilter


def _services():
    return current_app.extensions["services"]


def _month_now():
    return date.today().strftime("%Y-%m")


def _prev_month(month_str):
    y, m = map(int, month_str.split("-"))
    if m == 1:
        return f"{y-1}-12"
    return f"{y}-{m-1:02d}"


def _last_n_months(n, end_month):
    out = []
    cur = end_month
    for _ in range(n):
        out.append(cur)
        cur = _prev_month(cur)
    return list(reversed(out))


def _sum_kind_month(month, kind):
    flt = TransactionFilter(month=month, kind=kind)
    rows = _services().transactions.query(flt)
    s = Decimal("0.00")
    for t in rows:
        s += t.total_with_vat()
    return s


@bp.get("/dashboard", strict_slashes=False)
def api_dashboard():
    """
    GET /api/dashboard
    Summary: Summary for a month + 6-month trend

    Query:
      - month: "YYYY-MM" (optional; defaults to current month)

    Responses:
      200:
        data:
          {
            "month":"YYYY-MM",
            "total_exp": number,
            "total_inc": number,
            "sections": {"Food": number, "...": number},
            "cats_exp": {"Groceries": number, "...": number},
            "months": ["YYYY-MM", ...],       # 6 items
            "series_inc": [number, ...],      # len=6
            "series_exp": [number, ...]       # len=6
          }
        error: null
    """
    month = request.args.get("month") or _month_now()
    sections = _services().transactions.totals_by_section(month)
    cats_exp = _services().transactions.totals_by_category(month, TransactionKind.expense)
    total_exp = sum(sections.values(), Decimal("0.00"))
    total_inc = _sum_kind_month(month, TransactionKind.income)
    months = _last_n_months(6, month)
    series_inc = [float(_sum_kind_month(m, TransactionKind.income)) for m in months]
    series_exp = [float(_sum_kind_month(m, TransactionKind.expense)) for m in months]
    payload = {
        "month": month,
        "total_exp": float(total_exp),
        "total_inc": float(total_inc),
        "sections": {k.value: float(v) for k, v in sections.items()},
        "cats_exp": {k: float(v) for k, v in cats_exp.items()},
        "months": months,
        "series_inc": series_inc,
        "series_exp": series_exp
    }
    return make_response(payload)
