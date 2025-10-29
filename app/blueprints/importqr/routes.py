import uuid
from datetime import datetime
from decimal import Decimal
from flask import render_template, request, flash, redirect, url_for, current_app
from . import bp
from .forms import ImportQrForm
from app.core.domain import Transaction, TransactionKind

def _services():
    return current_app.extensions["services"]

def _parse_date_any(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            try:
                return datetime.strptime(s, "%d.%m.%Y").date()
            except Exception:
                return None

@bp.route("/", methods=["GET", "POST"])
def index():
    form = ImportQrForm()
    parsed = None
    if form.validate_on_submit():
        items = []
        if form.file.data:
            items = _services().qr_parser.parse(form.file.data)
        elif form.payload.data:
            items = _services().qr_parser.parse(form.payload.data)
        parsed = []
        for it in items:
            vd = _services().ekasa.validate(it.get("OPD", ""))
            dt = _parse_date_any(it.get("date") or "")
            parsed.append({
                "valid": bool(vd.get("valid")),
                "opd": it.get("OPD", ""),
                "date": dt.isoformat() if dt else "",
                "category": it.get("category", "Jedlo"),
                "item": it.get("item", ""),
                "qnt": str(it.get("qnt", "1")),
                "price": str(it.get("price", "0")),
                "vat": str(it.get("vat", "0")),
                "seller": it.get("seller", ""),
                "unit": it.get("unit", "ks"),
            })
        if form.submit_confirm.data and parsed:
            created = 0
            for it in parsed:
                try:
                    tx = Transaction(
                        id=str(uuid.uuid4()),
                        kind=TransactionKind.expense,
                        date=_parse_date_any(it["date"]) or datetime.utcnow().date(),
                        category=it["category"] or "Jedlo",
                        subcategory=None,
                        item=it["item"] or None,
                        qty=Decimal(str(it["qnt"])),
                        unit_price=Decimal(str(it["price"])),
                        vat=Decimal(str(it["vat"])) if it["vat"] else Decimal("0"),
                        seller=it["seller"] or None,
                        unit=it["unit"] or None,
                        note=it["opd"] or None,
                        source="qr",
                    )
                    _services().transactions.add(tx)
                    created += 1
                except Exception:
                    continue
            flash(f"Import hotovy. Pridanych poloziek: {created}.", "success")
            return redirect(url_for("transactions.list_view"))
        if not parsed:
            flash("Nepodarilo sa precitat ziadne polozky.", "warning")
    return render_template("importqr/index.html", form=form, parsed=parsed)
