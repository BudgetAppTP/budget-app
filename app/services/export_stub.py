import csv
from io import StringIO, BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from decimal import Decimal
from typing import Optional
from datetime import datetime
from app.core.domain import Transaction
from app.core.dto import TransactionFilter
from .repositories import TransactionsRepository

class ExportServiceStub:
    def __init__(self, tx_repo: TransactionsRepository):
        self.tx_repo = tx_repo

    def export_csv(self, month: Optional[str]) -> tuple[bytes, str]:
        flt = TransactionFilter(month=month)
        rows = self.tx_repo.query(flt) if month else self.tx_repo.all()
        sio = StringIO()
        w = csv.writer(sio, delimiter=",")
        w.writerow(["date", "kind", "category", "subcategory", "item", "qty", "unit_price", "vat", "seller", "unit", "note", "total_with_vat"])
        for t in rows:
            w.writerow([
                t.date.isoformat(),
                t.kind.value,
                t.category,
                t.subcategory or "",
                t.item or "",
                str(t.qty),
                str(t.unit_price),
                str(t.vat),
                t.seller or "",
                t.unit or "",
                t.note or "",
                str(t.total_with_vat()),
            ])
        data = sio.getvalue().encode("utf-8")
        name = f"export_{month or 'all'}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
        return data, name

    def export_pdf(self, month: Optional[str]) -> tuple[bytes, str]:
        bio = BytesIO()
        c = canvas.Canvas(bio, pagesize=A4)
        c.setTitle("Budget Export")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, 800, "Export osobneho rozpoctu")
        c.setFont("Helvetica", 11)
        c.drawString(72, 780, f"Mesiac: {month or 'vsetko'}")
        c.drawString(72, 760, "Tento PDF je placeholder pre demonstraciu.")
        c.showPage()
        c.save()
        bio.seek(0)
        name = f"export_{month or 'all'}.pdf"
        return bio.read(), name
