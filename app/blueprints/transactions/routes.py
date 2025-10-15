import uuid
from flask import render_template, request, redirect, url_for, flash, current_app
from . import bp
from .forms import TransactionFilterForm, IncomeForm, ExpenseForm
from app.core.dto import TransactionFilter
from app.core.domain import Transaction, TransactionKind

def _services():
    return current_app.extensions["services"]

@bp.get("/")
def list_view():
    form = TransactionFilterForm(request.args)
    flt = TransactionFilter(
        month=form.month.data or None,
        category=form.category.data or None if form.category.data else None,
        kind=TransactionKind(form.kind.data) if form.kind.data else None,
        search=form.search.data or None,
    )
    rows = _services().transactions.query(flt)
    total = sum([t.total_with_vat() for t in rows])
    return render_template("transactions/list.html", form=form, rows=rows, total=total)

@bp.route("/new-income", methods=["GET", "POST"])
def new_income():
    form = IncomeForm()
    if form.validate_on_submit():
        tx = Transaction(
            id=str(uuid.uuid4()),
            kind=TransactionKind.income,
            date=form.date.data,
            category=form.category.data,
            subcategory=form.subcategory.data or None,
            item=form.item.data or None,
            qty=form.qty.data,
            unit_price=form.unit_price.data,
            vat=form.vat.data or 0,
            seller=form.seller.data or None,
            unit=form.unit.data or None,
            note=form.note.data or None,
            source="manual",
        )
        _services().transactions.add(tx)
        flash("Prijem bol pridany.", "success")
        return redirect(url_for("transactions.list_view"))
    return render_template("transactions/create_income.html", form=form)

@bp.route("/new-expense", methods=["GET", "POST"])
def new_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        tx = Transaction(
            id=str(uuid.uuid4()),
            kind=TransactionKind.expense,
            date=form.date.data,
            category=form.category.data,
            subcategory=form.subcategory.data or None,
            item=form.item.data or None,
            qty=form.qty.data,
            unit_price=form.unit_price.data,
            vat=form.vat.data or 0,
            seller=form.seller.data or None,
            unit=form.unit.data or None,
            note=form.note.data or None,
            source="manual",
        )
        _services().transactions.add(tx)
        flash("Vydavok bol pridany.", "success")
        return redirect(url_for("transactions.list_view"))
    return render_template("transactions/create_expense.html", form=form)
