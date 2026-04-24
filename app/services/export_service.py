import csv
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO, StringIO
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Income, Receipt, ReceiptItem
from app.services.accounts_service import find_main_account


@dataclass
class ExportRow:
    date: str
    kind: str
    description: str
    amount: Decimal
    currency: str
    account_name: str
    tag: str
    category: str
    receipt_id: str
    receipt_item_id: str


def _parse_month_range(month: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    if month is None or not str(month).strip():
        return None, None

    month = str(month).strip()
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("Invalid month format, expected YYYY-MM")

    year = int(month[:4])
    month_num = int(month[5:7])
    if month_num < 1 or month_num > 12:
        raise ValueError("Month must be between 01 and 12")

    start = date(year, month_num, 1)
    end = date(year + 1, 1, 1) if month_num == 12 else date(year, month_num + 1, 1)
    return start, end


def _income_rows(user_id: uuid.UUID, month: Optional[str], currency: str, account_name: str) -> list[ExportRow]:
    start, end = _parse_month_range(month)
    query = db.session.query(Income).filter(Income.user_id == user_id)

    if start is not None and end is not None:
        query = query.filter(Income.income_date >= start, Income.income_date < end)

    rows = []
    for income in query.order_by(Income.income_date.asc(), Income.id.asc()).all():
        rows.append(
            ExportRow(
                date=income.income_date.isoformat(),
                kind="income",
                description=income.description or "",
                amount=Decimal(str(income.amount or 0)),
                currency=currency,
                account_name=account_name,
                tag=income.tag.name if income.tag else "",
                category="",
                receipt_id="",
                receipt_item_id="",
            )
        )
    return rows


def _expense_rows(user_id: uuid.UUID, month: Optional[str], currency: str) -> list[ExportRow]:
    start, end = _parse_month_range(month)
    query = (
        db.session.query(Receipt)
        .options(
            joinedload(Receipt.items).joinedload(ReceiptItem.category),
            joinedload(Receipt.tag),
            joinedload(Receipt.account),
        )
        .filter(Receipt.user_id == user_id)
    )

    if start is not None and end is not None:
        query = query.filter(Receipt.issue_date >= start, Receipt.issue_date < end)

    rows = []
    for receipt in query.order_by(Receipt.issue_date.asc(), Receipt.created_at.asc().nullslast(), Receipt.id.asc()).all():
        base = {
            "date": receipt.issue_date.isoformat(),
            "kind": "expense",
            "currency": receipt.account.currency if receipt.account else currency,
            "account_name": receipt.account.name if receipt.account else "",
            "tag": receipt.tag.name if receipt.tag else "",
            "receipt_id": str(receipt.id),
        }

        if receipt.items:
            for item in receipt.items:
                rows.append(
                    ExportRow(
                        date=base["date"],
                        kind=base["kind"],
                        description=item.name or receipt.description or "",
                        amount=Decimal(str(item.total_price or 0)),
                        currency=base["currency"],
                        account_name=base["account_name"],
                        tag=base["tag"],
                        category=item.category.name if item.category else "",
                        receipt_id=base["receipt_id"],
                        receipt_item_id=str(item.id),
                    )
                )
        else:
            rows.append(
                ExportRow(
                    date=base["date"],
                    kind=base["kind"],
                    description=receipt.description or "",
                    amount=Decimal(str(receipt.total_amount or 0)),
                    currency=base["currency"],
                    account_name=base["account_name"],
                    tag=base["tag"],
                    category="",
                    receipt_id=base["receipt_id"],
                    receipt_item_id="",
                )
            )
    return rows


def _export_rows(user_id: uuid.UUID, month: Optional[str]) -> list[ExportRow]:
    account = find_main_account(user_id)
    currency = account.currency
    account_name = account.name
    rows = _income_rows(user_id, month, currency, account_name)
    rows.extend(_expense_rows(user_id, month, currency))
    rows.sort(key=lambda row: (row.date, row.kind, row.description, row.receipt_id, row.receipt_item_id))
    return rows


def export_csv(user_id: uuid.UUID, month: Optional[str]) -> tuple[bytes, str]:
    rows = _export_rows(user_id, month)
    sio = StringIO()
    writer = csv.writer(sio, delimiter=",")
    writer.writerow(
        [
            "date",
            "kind",
            "description",
            "amount",
            "currency",
            "account_name",
            "tag",
            "category",
            "receipt_id",
            "receipt_item_id",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.date,
                row.kind,
                row.description,
                str(row.amount),
                row.currency,
                row.account_name,
                row.tag,
                row.category,
                row.receipt_id,
                row.receipt_item_id,
            ]
        )

    data = sio.getvalue().encode("utf-8")
    name = f"export_{month or 'all'}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
    return data, name


def export_pdf(user_id: uuid.UUID, month: Optional[str]) -> tuple[bytes, str]:
    rows = _export_rows(user_id, month)
    income_total = sum((row.amount for row in rows if row.kind == "income"), Decimal("0.00"))
    expense_total = sum((row.amount for row in rows if row.kind == "expense"), Decimal("0.00"))

    bio = BytesIO()
    pdf = canvas.Canvas(bio, pagesize=A4)
    y = 800

    def line(text: str, font: str = "Helvetica", size: int = 10, step: int = 14):
        nonlocal y
        if y < 50:
            pdf.showPage()
            y = 800
        pdf.setFont(font, size)
        pdf.drawString(40, y, text[:110])
        y -= step

    pdf.setTitle("Budget Export")
    line("Budget Export", font="Helvetica-Bold", size=14, step=18)
    line(f"Month: {month or 'all'}")
    line(f"Total incomes: {income_total}")
    line(f"Total expenses: {expense_total}")
    line(f"Balance: {income_total - expense_total}", step=18)
    line("Rows", font="Helvetica-Bold", size=12)

    for row in rows:
        detail = f"{row.date} | {row.kind} | {row.description or '-'} | {row.amount} {row.currency}"
        if row.category:
            detail += f" | {row.category}"
        elif row.tag:
            detail += f" | {row.tag}"
        line(detail)

    if not rows:
        line("No data available for the selected period.")

    pdf.save()
    bio.seek(0)
    return bio.read(), f"export_{month or 'all'}.pdf"
