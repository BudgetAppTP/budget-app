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

@bp.get("/budgets")
def api_budgets_get():
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

@bp.put("/budgets/<month>")
def api_budgets_upsert(month):
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
