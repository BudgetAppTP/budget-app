import uuid
from decimal import Decimal
from datetime import date
from flask import render_template, request, redirect, url_for, flash, current_app
from . import bp
from .forms import MonthSelectForm, BudgetItemForm, BudgetListForm
from app.core.domain import MonthlyBudget, Section

def _services():
    return current_app.extensions["services"]

def _current_month():
    return date.today().strftime("%Y-%m")

@bp.route("/", methods=["GET", "POST"])
def index():
    form = MonthSelectForm(request.values)
    month = form.month.data or _current_month()
    tx_totals = _services().transactions.totals_by_section(month)
    budgets = _services().budgets.by_month(month)
    if not budgets:
        for s in _services().budgets.sections():
            _services().budgets.upsert(MonthlyBudget(str(uuid.uuid4()), month, s, Decimal("0.00"), Decimal("0")))
        budgets = _services().budgets.by_month(month)
    data = []
    for b in budgets:
        spent = tx_totals.get(b.section, Decimal("0.00"))
        data.append({"b": b, "spent": spent})
    return render_template("budgets/index.html", form=form, month=month, data=data)

@bp.route("/<month>", methods=["GET", "POST"])
def detail(month):
    budgets = _services().budgets.by_month(month)
    if not budgets:
        for s in _services().budgets.sections():
            _services().budgets.upsert(MonthlyBudget(str(uuid.uuid4()), month, s, Decimal("0.00"), Decimal("0")))
        budgets = _services().budgets.by_month(month)
    if request.method == "POST":
        for b in budgets:
            lid = request.form.get(f"id_{b.section.value}")
            lim = request.form.get(f"limit_{b.section.value}")
            pct = request.form.get(f"pct_{b.section.value}")
            if lim is not None:
                try:
                    lim_dec = Decimal(str(lim))
                except Exception:
                    lim_dec = b.limit_amount
            else:
                lim_dec = b.limit_amount
            if pct is not None and len(str(pct)) > 0:
                try:
                    pct_dec = Decimal(str(pct))
                except Exception:
                    pct_dec = b.percent_target
            else:
                pct_dec = b.percent_target
            _services().budgets.upsert(MonthlyBudget(lid or b.id, month, b.section, lim_dec, pct_dec))
        flash("Rozpocet bol ulozeny.", "success")
        return redirect(url_for("budgets.detail", month=month))
    tx_totals = _services().transactions.totals_by_section(month)
    rows = []
    for b in budgets:
        spent = tx_totals.get(b.section, Decimal("0.00"))
        rows.append({"b": b, "spent": spent})
    return render_template("budgets/detail.html", month=month, rows=rows)
