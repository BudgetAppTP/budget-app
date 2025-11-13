from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import date
from decimal import Decimal
import uuid
from app.core.domain import MonthlyBudget

from . import bp


def _services():
    from flask import current_app
    return current_app.extensions["services"]


def _current_month():
    return date.today().strftime("%Y-%m")

tables = {
    "sporenie": [
        {"id": 1, "popis": "rezerva", "budget": 300.00, "extra1": "núdzový fond"},
        {"id": 2, "popis": "auto", "budget": 250.00, "extra1": "servis"},
        {"id": 3, "popis": "materská", "budget": 150.00, "extra1": "deti"},
        {"id": 4, "popis": "svadba", "budget": 100.00, "extra1": "darček"},
    ],
    "investovanie": [
        {"id": 1, "popis": "ETF Degiro", "budget": 150.00, "extra1": "Degiro", "extra2": "S&P 500"},
        {"id": 2, "popis": "Crypto Binance", "budget": 50.00, "extra1": "Binance", "extra2": "BTC"},
        {"id": 3, "popis": "Akcie Revolut", "budget": 100.00, "extra1": "Revolut", "extra2": "Tesla"},
    ],
    "potreby": [
        {"id": 1, "popis": "Bývanie", "budget": 400.00, "extra1": "nájom"},
        {"id": 2, "popis": "Jedlo", "budget": 250.00, "extra1": "potraviny"},
        {"id": 3, "popis": "Doprava", "budget": 120.00, "extra1": "mesačník"},
        {"id": 4, "popis": "Zdravie", "budget": 80.00, "extra1": "lekáreň"},
    ],
    "volny_cas": [
        {"id": 1, "popis": "Kino", "budget": 40.00, "extra1": "zábava"},
        {"id": 2, "popis": "Kaviareň", "budget": 60.00, "extra1": "oddych"},
        {"id": 3, "popis": "Výlet", "budget": 100.00, "extra1": "víkend"},
        {"id": 4, "popis": "Knihy", "budget": 30.00, "extra1": "vzdelanie"},
    ],
}


@bp.route("/", methods=["GET", "POST"])
def index():
    form = None
    month = _current_month()
    tx_totals = _services().transactions.totals_by_section(month)
    budgets = _services().budgets.by_month(month)

    if not budgets:
        for s in _services().budgets.sections():
            _services().budgets.upsert(
                MonthlyBudget(str(uuid.uuid4()), month, s, Decimal("0.00"), Decimal("0"))
            )
        budgets = _services().budgets.by_month(month)

    data = []
    for b in budgets:
        spent = tx_totals.get(b.section, Decimal("0.00"))
        data.append({"b": b, "spent": spent})

    zostatok = sum([d["b"].limit_amount - d["spent"] for d in data])

    table_meta = []
    for name, rows in tables.items():
        if rows:
            columns = list(rows[0].keys())
            table_meta.append({
                "name": name,
                "columns": columns,
                "rows": rows
            })

    return render_template(
        "budgets/index.html",
        month=month,
        data=data,
        zostatok=zostatok,
        table_meta=table_meta
    )


@bp.route("/add", methods=["POST"])
def add_record():
    table_name = request.form.get("table")

    if table_name not in tables:
        return jsonify({"error": "unknown table"}), 400

    new_id = max([r["id"] for r in tables[table_name]]) + 1 if tables[table_name] else 1
    new_row = {"id": new_id}

    for key, value in request.form.items():
        if key != "table":
            new_row[key] = value

    tables[table_name].append(new_row)
    return redirect(url_for("budgets.index"))


@bp.route("/delete/<table>/<int:row_id>", methods=["POST"])
def delete_record(table, row_id):
    if table in tables:
        tables[table] = [r for r in tables[table] if r["id"] != row_id]
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Unknown table"}), 400


@bp.route("/edit/<table>/<int:row_id>", methods=["POST"])
def edit_record(table, row_id):
    if table not in tables:
        return jsonify({"error": "unknown table"}), 400

    data = request.json
    for r in tables[table]:
        if r["id"] == row_id:
            r.update(data)
    return jsonify({"success": True, "updated": data})