import json
from decimal import Decimal

class QrParserStub:
    def parse(self, payload):
        if hasattr(payload, "read"):
            data = payload.read()
            try:
                obj = json.loads(data.decode("utf-8"))
            except Exception:
                return []
        elif isinstance(payload, (str, bytes)):
            try:
                obj = json.loads(payload if isinstance(payload, str) else payload.decode("utf-8"))
            except Exception:
                return []
        else:
            return []
        items = obj if isinstance(obj, list) else obj.get("items", [])
        out = []
        for it in items:
            out.append({
                "OPD": str(it.get("OPD") or it.get("opd") or ""),
                "date": str(it.get("date") or it.get("datum") or ""),
                "category": str(it.get("category") or it.get("kategoria") or "Jedlo"),
                "item": str(it.get("item") or it.get("polozka") or ""),
                "qnt": self._dec(it.get("qnt") or it.get("qty") or 1),
                "price": self._dec(it.get("price") or it.get("cena") or 0),
                "vat": self._dec(it.get("vat") or it.get("dph") or 0),
                "seller": str(it.get("seller") or it.get("predajca") or ""),
                "unit": str(it.get("unit") or it.get("jednotka") or "ks"),
            })
        return out

    def _dec(self, v):
        s = str(v).replace(" ", "")
        if "," in s and "." not in s:
            s = s.replace(",", ".")
        return Decimal(s)
