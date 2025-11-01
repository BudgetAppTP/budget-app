import uuid
from datetime import datetime
from decimal import Decimal
from flask import current_app, request
from app.api import bp, make_response
from app.core.domain import Transaction, TransactionKind

def _services():
    return current_app.extensions["services"]

def _parse_date_any(s):
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

@bp.post("/import-qr/preview")
def api_importqr_preview():
    body = request.get_json(silent=True) or {}
    payload = body.get("payload")
    items = []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, str):
        items = _services().qr_parser.parse(payload)
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
    return make_response({"items": parsed, "count": len(parsed)})

@bp.post("/import-qr/confirm")
def api_importqr_confirm():
    body = request.get_json(silent=True) or {}
    items = body.get("items") or []
    created = 0
    for it in items:
        try:
            tx = Transaction(
                id=str(uuid.uuid4()),
                kind=TransactionKind.expense,
                date=_parse_date_any(it.get("date")) or datetime.utcnow().date(),
                category=it.get("category") or "Jedlo",
                subcategory=None,
                item=it.get("item") or None,
                qty=Decimal(str(it.get("qnt", "1"))),
                unit_price=Decimal(str(it.get("price", "0"))),
                vat=Decimal(str(it.get("vat"))) if it.get("vat") else Decimal("0"),
                seller=it.get("seller") or None,
                unit=it.get("unit") or None,
                note=it.get("opd") or None,
                source="qr",
            )
            _services().transactions.add(tx)
            created += 1
        except Exception:
            continue
    return make_response({"created": created})
