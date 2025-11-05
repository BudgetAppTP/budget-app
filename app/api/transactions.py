"""
Transactions API

Paths:
  - GET  /api/transactions/      List with filters
  - POST /api/transactions/      Create income or expense

Filters:
  - month=YYYY-MM
  - kind=income|expense
  - category=string
  - search=text (matches description)

Notes:
- Демоданные используются как заглушка. Ответ в конверте {data,error}.
"""

from flask import request
from app.api import bp, make_response

demo_incomes = [
    {"id": 1, "date": "2025-10-01", "description": "Výplata", "amount": 1200.00, "kind": "income"},
    {"id": 2, "date": "2025-10-05", "description": "Darček od babky", "amount": 200.00, "kind": "income"},
    {"id": 3, "date": "2025-10-10", "description": "Predaj starého bicykla", "amount": 350.00, "kind": "income"},
]

demo_expenses = [
    {"id": 1, "date": "2025-10-02", "category": "Jedlo", "amount": 45.20, "kind": "expense"},
    {"id": 2, "date": "2025-10-05", "category": "Doprava", "amount": 14.00, "kind": "expense"},
    {"id": 3, "date": "2025-10-07", "category": "Byvanie", "amount": 865.00, "kind": "expense"},
]


def _all_tx():
    return demo_incomes + demo_expenses


@bp.get("/transactions", strict_slashes=False)
def api_transactions_list():
    """
    GET /api/transactions/
    Summary: List transactions

    Query:
      - month: "YYYY-MM"
      - kind: "income" | "expense"
      - category: string
      - search: substring in description (case-insensitive)

    Responses:
      200:
        data: {"items":[{...}], "count": n}
        error: null
    """
    month = (request.args.get("month") or "").strip()
    kind = (request.args.get("kind") or "").strip()
    category = (request.args.get("category") or "").strip()
    search = (request.args.get("search") or "").strip().lower()
    rows = _all_tx()
    if kind in ("income", "expense"):
        rows = [r for r in rows if r.get("kind") == kind]
    if category:
        rows = [r for r in rows if r.get("category", "") == category]
    if month:
        rows = [r for r in rows if r.get("date", "").startswith(month)]
    if search:
        rows = [r for r in rows if search in str(r.get("description", "")).lower()]
    return make_response({"items": rows, "count": len(rows)})


@bp.post("/transactions", strict_slashes=False)
def api_transactions_create():
    """
    POST /api/transactions/
    Summary: Create transaction (income or expense)

    Request (JSON):
      Income:
        {"kind":"income","date":"YYYY-MM-DD","description":"...","amount":120.0}
      Expense:
        {"kind":"expense","date":"YYYY-MM-DD","category":"Jedlo","amount":14.5}

    Responses:
      201:
        data: {"id": <int>, "...": "...", "kind":"income|expense"}
        error: null
      400:
        data: null
        error: {"code":"bad_request","message":"kind must be income or expense"}
    """
    p = request.get_json(silent=True) or {}
    k = p.get("kind")
    if k == "income":
        new_id = (demo_incomes[-1]["id"] + 1) if demo_incomes else 1
        row = {
            "id": new_id,
            "date": p.get("date", ""),
            "description": p.get("description", ""),
            "amount": float(p.get("amount", 0)),
            "kind": "income",
        }
        demo_incomes.append(row)
        return make_response(row, None, 201)
    if k == "expense":
        new_id = (demo_expenses[-1]["id"] + 1) if demo_expenses else 1
        row = {
            "id": new_id,
            "date": p.get("date", ""),
            "category": p.get("category", ""),
            "amount": float(p.get("amount", 0)),
            "kind": "expense",
        }
        demo_expenses.append(row)
        return make_response(row, None, 201)
    return make_response(None, {"code": "bad_request", "message": "kind must be income or expense"}, 400)
