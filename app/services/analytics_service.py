# app/services/analytics_service.py
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func

from app.extensions import db
from app.models import Receipt, ReceiptItem, Category, Tag
from app.services import accounts_service
from app.services.errors import BadRequestError
from app.services.responses import OkResult


def get_donut_data(
    year: int | None = None,
    month: int | None = None,
    user_id: uuid.UUID | None = None,
):
    if (year is None) or (month is None):
        raise BadRequestError("Both year and month must be provided together")

    if not (1 <= year <= 9999):
        raise BadRequestError("Year must be a valid calendar year")

    if not (1 <= month <= 12):
        raise BadRequestError("Month must be between 1 and 12")

    account = accounts_service.find_main_account(user_id)

    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    # TOTAL
    total_q = (
        db.session.query(func.coalesce(func.sum(ReceiptItem.total_price), 0))
        .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
        .filter(Receipt.issue_date >= start, Receipt.issue_date < end)
        .filter(Receipt.user_id == user_id)
        .filter(Receipt.account_id == account.id)
    )

    total_amount = float(total_q.scalar() or 0.0)

    # CATEGORIES
    cat_q = (
        db.session.query(
            func.coalesce(Category.name, "Uncategorized").label("category"),
            func.coalesce(func.sum(ReceiptItem.total_price), 0).label("amount"),
        )
        .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
        .outerjoin(Category, ReceiptItem.category_id == Category.id)
        .filter(Receipt.issue_date >= start, Receipt.issue_date < end)
        .filter(Receipt.user_id == user_id)
        .filter(Receipt.account_id == account.id)
        .group_by(func.coalesce(Category.name, "Uncategorized"))
        .order_by(func.coalesce(func.sum(ReceiptItem.total_price), 0).desc())
    )

    categories = []
    for category, amount in cat_q.all():
        amount_f = float(amount or 0.0)
        percentage = (amount_f / total_amount * 100.0) if total_amount > 0 else 0.0
        categories.append({
            "category": category,
            "amount": round(amount_f, 2),
            "percentage": round(percentage, 1),
        })

    # TAGS_BY_CATEGORY: category -> tag -> date -> sum
    detail_q = (
        db.session.query(
            func.coalesce(Category.name, "Uncategorized").label("category"),
            func.coalesce(Tag.name, "No tag").label("tag"),
            Receipt.issue_date.label("issue_date"),
            func.coalesce(func.sum(ReceiptItem.total_price), 0).label("amount"),
        )
        .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
        .outerjoin(Category, ReceiptItem.category_id == Category.id)
        .outerjoin(Tag, Receipt.tag_id == Tag.id)
        .filter(Receipt.issue_date >= start, Receipt.issue_date < end)
        .filter(Receipt.user_id == user_id)
        .filter(Receipt.account_id == account.id)
        .group_by(
            func.coalesce(Category.name, "Uncategorized"),
            func.coalesce(Tag.name, "No tag"),
            Receipt.issue_date,
        )
        .order_by(
            func.coalesce(Category.name, "Uncategorized").asc(),
            func.coalesce(Tag.name, "No tag").asc(),
            Receipt.issue_date.asc(),
        )
    )

    tags_by_category: dict[str, dict[str, dict[str, float]]] = {}

    for category, tag, issue_date, amount in detail_q.all():
        tags_by_category.setdefault(category, {})
        tags_by_category[category].setdefault(tag, {})
        tags_by_category[category][tag][issue_date.isoformat()] = round(float(amount or 0.0), 2)

    return OkResult({
        "year": year,
        "month": month,
        "total_amount": round(total_amount, 2),
        "categories": categories,
        "tags_by_category": tags_by_category,
    })
