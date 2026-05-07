import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import AccountMember, Receipt, ReceiptItem, Tag
from app.services import ekasa_service, tags_service
from app.services.errors import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.services.responses import CreatedResult, OkResult
from app.validators.common_validators import MonthYearFilter, parse_uuid_field
from app.validators.receipt_validators import (
    validate_receipt_create_data,
    validate_receipt_update_data,
)

ALLOWED_RECEIPT_SORT_FIELDS = {
    "issue_date": Receipt.issue_date,
    "total_amount": Receipt.total_amount,
}


def _receipt_currency(receipt: Receipt) -> str | None:
    return receipt.account.currency if receipt.account is not None else None


def _serialize_receipt(receipt: Receipt) -> dict:
    return {
        "id": str(receipt.id),
        "external_uid": receipt.external_uid,
        "tag": receipt.tag.name if receipt.tag else None,
        "tag_id": str(receipt.tag_id) if receipt.tag_id else None,
        "description": receipt.description,
        "issue_date": receipt.issue_date.isoformat() if receipt.issue_date else None,
        "currency": _receipt_currency(receipt),
        "total_amount": float(receipt.total_amount) if receipt.total_amount is not None else None,
        "extra_metadata": receipt.extra_metadata,
        "user_id": str(receipt.user_id),
        "account_id": str(receipt.account_id),
        "created_at": receipt.created_at.isoformat() if receipt.created_at else None,
    }


def _owned_receipts_query(user_id: uuid.UUID):
    return db.session.query(Receipt).filter(Receipt.user_id == user_id)


def _get_receipt_for_user(
    receipt_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    lock: bool = False,
) -> Receipt:
    query = (
        _owned_receipts_query(user_id)
        .options(
            joinedload(Receipt.account),
            joinedload(Receipt.tag),
        )
        .filter(Receipt.id == receipt_id)
    )
    if lock:
        query = query.with_for_update()

    receipt = query.first()
    if receipt is None:
        raise NotFoundError("Receipt not found")
    return receipt


def _load_tag_for_user(user_id: uuid.UUID, tag_id: uuid.UUID | None) -> Tag | None:
    if tag_id is None:
        return None

    tag = db.session.get(Tag, tag_id)
    if not tag:
        raise NotFoundError("Tag not found")
    if tag.user_id != user_id:
        raise ForbiddenError("Tag does not belong to this user")
    return tag


def _ensure_account_membership(user_id: uuid.UUID, account_id: uuid.UUID) -> None:
    membership = (
        db.session.query(AccountMember)
        .filter(
            AccountMember.user_id == user_id,
            AccountMember.account_id == account_id,
        )
        .first()
    )
    if membership is None:
        raise ForbiddenError("User is not a member of this account")


def _resolve_account_for_user(
    user_id: uuid.UUID,
    account_id: uuid.UUID | None,
) -> uuid.UUID:
    if account_id is not None:
        _ensure_account_membership(user_id, account_id)
        return account_id

    default_membership = (
        db.session.query(AccountMember)
        .filter(AccountMember.user_id == user_id)
        .order_by(AccountMember.created_at.asc())
        .first()
    )
    if default_membership is None:
        raise BadRequestError("Missing account_id and user has no account membership")
    return default_membership.account_id


def get_all_receipts(
    user_id: uuid.UUID,
    month_filter: MonthYearFilter,
    *,
    sort_by: str = "issue_date",
    descending: bool = True,
    account_id: uuid.UUID | None = None,
):
    if sort_by not in ALLOWED_RECEIPT_SORT_FIELDS:
        raise BadRequestError("Invalid sort field")

    query = _owned_receipts_query(user_id).options(
        joinedload(Receipt.account),
        joinedload(Receipt.tag),
    )

    start, end = month_filter.range()
    if start is not None and end is not None:
        query = query.filter(
            Receipt.issue_date >= start,
            Receipt.issue_date < end,
        )

    if account_id is not None:
        _ensure_account_membership(user_id, account_id)
        query = query.filter(Receipt.account_id == account_id)

    order_column = ALLOWED_RECEIPT_SORT_FIELDS[sort_by]
    query = query.order_by(order_column.desc() if descending else order_column.asc())

    receipts = query.all()
    return OkResult([_serialize_receipt(receipt) for receipt in receipts])


def create_receipt(data: dict, user_id: uuid.UUID):
    validated = validate_receipt_create_data(data)
    account_id = _resolve_account_for_user(user_id, validated["account_id"])
    tag = _load_tag_for_user(user_id, validated["tag_id"])

    receipt = Receipt(
        user_id=user_id,
        account_id=account_id,
        tag=tag,
        description=validated["description"],
        issue_date=validated["issue_date"],
        total_amount=validated["total_amount"],
        external_uid=validated["external_uid"],
        extra_metadata=validated["extra_metadata"],
    )

    try:
        db.session.add(receipt)
        if tag is not None:
            tags_service.register_tag_assigned(tag)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return CreatedResult(
        {"id": str(receipt.id), "message": "Receipt created successfully"}
    )


def get_receipt_by_id(receipt_id: uuid.UUID, user_id: uuid.UUID):
    receipt = _get_receipt_for_user(receipt_id, user_id)
    return OkResult(_serialize_receipt(receipt))


def update_receipt(receipt_id: uuid.UUID, data: dict, user_id: uuid.UUID):
    receipt = _get_receipt_for_user(receipt_id, user_id, lock=True)
    validated = validate_receipt_update_data(data)

    old_tag = receipt.tag
    new_tag = old_tag

    if "tag_id" in validated:
        new_tag = _load_tag_for_user(user_id, validated["tag_id"])

    if new_tag is not old_tag:
        if old_tag is not None:
            receipt.tag = None
            tags_service.register_tag_unassigned(old_tag)

        if new_tag is not None:
            receipt.tag = new_tag
            tags_service.register_tag_assigned(new_tag)

    if "description" in validated:
        receipt.description = validated["description"]
    if "issue_date" in validated:
        receipt.issue_date = validated["issue_date"]
    if "total_amount" in validated:
        receipt.total_amount = validated["total_amount"]
    if "external_uid" in validated:
        receipt.external_uid = validated["external_uid"]
    if "extra_metadata" in validated:
        receipt.extra_metadata = validated["extra_metadata"]

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult(
        {"id": str(receipt.id), "message": "Receipt updated successfully"}
    )


def delete_receipt(receipt_id: uuid.UUID, user_id: uuid.UUID):
    receipt = _get_receipt_for_user(receipt_id, user_id, lock=True)
    tag = receipt.tag

    try:
        db.session.delete(receipt)

        if tag is not None:
            tags_service.register_tag_unassigned(tag)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult({"message": "Receipt deleted successfully"})


def import_receipt_from_ekasa(data: dict, user_id: uuid.UUID):
    receipt_id = str(data.get("receipt_id", "")).strip()
    if not receipt_id:
        raise BadRequestError("Missing receipt_id")

    account_id = _resolve_account_for_user(
        user_id,
        parse_uuid_field(
            data.get("account_id"),
            "account_id",
            required=False,
        ),
    )

    ekasa_data = ekasa_service.fetch_receipt_data(receipt_id)
    receipt_payload = ekasa_data["receipt"]
    external_uid = receipt_payload.get("receiptId")

    existing = (
        db.session.query(Receipt)
        .filter(Receipt.external_uid == external_uid)
        .first()
    )
    if existing:
        raise ConflictError("Receipt already imported")

    try:
        issue_date = datetime.strptime(
            receipt_payload["issueDate"],
            "%d.%m.%Y %H:%M:%S",
        ).date()
        total_price = Decimal(str(receipt_payload.get("totalPrice", 0)))
    except (KeyError, ValueError, TypeError) as exc:
        raise BadRequestError("Invalid receipt data returned by eKasa") from exc

    organization = receipt_payload.get("organization")
    tag = None
    if organization:
        tag = tags_service.find_or_create_tag_from_ekasa(user_id, organization)

    description = (
        organization.get("name")
        if organization and organization.get("name")
        else "eKasa receipt"
    )

    receipt = Receipt(
        user_id=user_id,
        account_id=account_id,
        tag=tag,
        description=description,
        issue_date=issue_date,
        total_amount=total_price,
        external_uid=external_uid,
        extra_metadata={
            "ico": receipt_payload.get("ico"),
            "dic": receipt_payload.get("dic"),
            "okp": receipt_payload.get("okp"),
            "unit": receipt_payload.get("unit", {}),
        },
    )

    items_payload = receipt_payload.get("items") or []
    if not isinstance(items_payload, list):
        items_payload = []

    try:
        db.session.add(receipt)

        if tag is not None:
            tags_service.register_tag_assigned(tag)

        for item_payload in items_payload:
            item = ReceiptItem(
                receipt=receipt,
                user_id=user_id,
                name=(item_payload.get("name") or "").strip(),
                quantity=Decimal(str(item_payload.get("quantity", 1))),
                unit_price=Decimal(str(item_payload.get("price", 0))),
                total_price=Decimal(str(item_payload.get("price", 0))),
                extra_metadata={
                    "vatRate": item_payload.get("vatRate"),
                    "itemType": item_payload.get("itemType"),
                },
            )
            db.session.add(item)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return CreatedResult(
        {
            "message": "Receipt imported successfully",
            "tag": tag.name if tag else None,
            "tag_id": str(tag.id) if tag else None,
            "receipt_id": str(receipt.id),
            "total_items": len(items_payload),
        }
    )


def get_ekasa_items(
    month_filter: MonthYearFilter,
    user_id: uuid.UUID,
    *,
    account_id: uuid.UUID | None = None,
):
    query = (
        _owned_receipts_query(user_id)
        .options(
            joinedload(Receipt.items),
            joinedload(Receipt.tag),
            joinedload(Receipt.account),
        )
        .filter(Receipt.external_uid.isnot(None))
    )

    start, end = month_filter.range()
    if start is not None and end is not None:
        query = query.filter(
            Receipt.issue_date >= start,
            Receipt.issue_date < end,
        )

    if account_id is not None:
        _ensure_account_membership(user_id, account_id)
        query = query.filter(Receipt.account_id == account_id)

    receipts = query.order_by(Receipt.issue_date.asc(), Receipt.created_at.asc()).all()

    checks = []
    total_items = 0

    for receipt in receipts:
        items = []
        for item in receipt.items or []:
            items.append(
                {
                    "id": str(item.id),
                    "name": item.name,
                    "quantity": float(item.quantity) if item.quantity is not None else None,
                    "unit_price": float(item.unit_price) if item.unit_price is not None else None,
                    "total_price": float(item.total_price) if item.total_price is not None else None,
                    "category_id": str(item.category_id) if item.category_id else None,
                    "extra_metadata": item.extra_metadata,
                }
            )

        total_items += len(items)
        checks.append(
            {
                "receipt_id": str(receipt.id),
                "external_uid": receipt.external_uid,
                "issue_date": receipt.issue_date.isoformat() if receipt.issue_date else None,
                "description": receipt.description,
                "currency": _receipt_currency(receipt),
                "total_amount": float(receipt.total_amount) if receipt.total_amount is not None else None,
                "tag": receipt.tag.name if receipt.tag else None,
                "tag_id": str(receipt.tag_id) if receipt.tag_id else None,
                "user_id": str(receipt.user_id),
                "account_id": str(receipt.account_id),
                "items": items,
            }
        )

    return OkResult(
        {
            "success": True,
            "checks": checks,
            "total_checks": len(checks),
            "total_items": total_items,
        }
    )
