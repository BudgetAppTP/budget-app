"""
Budgets API

Paths:
  - GET /api/budgets?month=YYYY-MM
  - PUT /api/budgets/{month}

Notes:
- Spent is computed from transactions service.
- If month has no rows, sections are auto-seeded with zero limits.
"""

from datetime import date
from decimal import Decimal
import uuid
from flask import current_app, request
from app.api import bp, make_response
from app.core.domain import MonthlyBudget


def _services():
    return current_app.extensions["services"]


def _current_month():
    return date.today().strftime("%Y-%m")


@bp.get("/budgets", strict_slashes=False)
def api_budgets_get():
    """
    GET /api/budgets
    Summary: Get budgets for a month

    Query:
      - month: "YYYY-MM" (optional; defaults to current month)

    Responses:
      200:
        data:
          {
            "month": "YYYY-MM",
            "items": [
              {"id":"...","month":"YYYY-MM","section":"Food","limit_amount":100.0,"percent_target":50.0,"spent":25.0}
            ],
            "left": 75.0
          }
        error: null
    """
    month = request.args.get("month") or _current_month()
    tx_totals = _services().transactions.totals_by_section(month)
    budgets = _services().budgets.by_month(month)
    if not budgets:
        for s in _services().budgets.sections():
            _services().budgets.upsert(MonthlyBudget(str(uuid.uuid4()), month, s, Decimal("0.00"), Decimal("0")))
        budgets = _services().budgets.by_month(month)
    items = []
    for b in budgets:
        spent = tx_totals.get(b.section, Decimal("0.00"))
        items.append({
            "id": b.id,
            "month": b.month,
            "section": str(b.section),
            "limit_amount": float(b.limit_amount),
            "percent_target": float(b.percent_target),
            "spent": float(spent),
        })
    total_left = float(sum([Decimal(str(i["limit_amount"])) - Decimal(str(i["spent"])) for i in items]))
    return make_response({"month": month, "items": items, "left": total_left})


@bp.put("/budgets/<month>", strict_slashes=False)
def api_budgets_upsert(month):
    """
    PUT /api/budgets/{month}
    Summary: Bulk upsert budget sections for a month

    Path:
      - month: "YYYY-MM"

    Request:
      {"items":[{"id":"...","section":"Food","limit_amount":100.0,"percent_target":50.0}, ...]}

    Responses:
      200:
        data: {"ok": true}
        error: null
    """
    body = request.get_json(silent=True) or {}
    rows = body.get("items", [])
    for r in rows:
        _services().budgets.upsert(
            MonthlyBudget(
                r.get("id") or str(uuid.uuid4()),
                month,
                r.get("section"),
                Decimal(str(r.get("limit_amount", 0))),
                Decimal(str(r.get("percent_target", 0))),
            )
        )
    return make_response({"ok": True})
