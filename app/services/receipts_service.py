import uuid
from decimal import Decimal

from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import AccountMember, Receipt, ReceiptItem, Tag
from datetime import date, datetime

from app.services import tags_service, ekasa_service


def _receipt_currency(receipt: Receipt) -> str | None:
    return receipt.account.currency if receipt.account is not None else None


def get_all_receipts(
    year: int | None = None,
    month: int | None = None,
    account_id: uuid.UUID | None = None,
):
    """
    Get all receipts.

    Optional filtering:
      - year + month: return only receipts that belong to given month/year.

    Args:
      year: int | None
      month: int | None (1..12)

    Returns:
      tuple: (payload: list|dict, status_code: int)

      payload example (success):
        [
          {"id":"...", "issue_date":"YYYY-MM-DD", "total_amount": 10.0, ...},
          ...
        ]
    """
    query = db.session.query(Receipt).options(
        joinedload(Receipt.account),
        joinedload(Receipt.tag),
    )

    # Filter by month/year (both must be provided together)
    if (year is None) ^ (month is None):
        return {"error": "Both year and month must be provided together"}, 400

    if year is not None and month is not None:
        if month < 1 or month > 12:
            return {"error": "Month must be between 1 and 12"}, 400

        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        query = query.filter(
            Receipt.issue_date >= start,
            Receipt.issue_date < end
        )

    if account_id is not None:
        query = query.filter(Receipt.account_id == account_id)

    receipts = query.all()

    result = []
    for r in receipts:
        result.append({
            "id": str(r.id),
            "external_uid": r.external_uid,
            "tag": r.tag.name if r.tag else None,
            "tag_id": str(r.tag_id) if r.tag_id else None,
            "description": getattr(r, "description", None),
            "issue_date": r.issue_date.isoformat() if r.issue_date else None,
            "currency": _receipt_currency(r),
            "total_amount": float(r.total_amount) if r.total_amount is not None else None,
            "extra_metadata": r.extra_metadata,
            "user_id": str(r.user_id),
            "account_id": str(r.account_id),
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return result, 200

def _parse_user_id(raw_user_id):
    """
    Parse user_id from payload.

    Returns:
      (user_id: UUID | None, error_body: dict | None, status: int | None)
    """
    if not raw_user_id:
        return None, {"error": "Missing user_id"}, 400

    if isinstance(raw_user_id, uuid.UUID):
        return raw_user_id, None, None

    if isinstance(raw_user_id, str):
        try:
            return uuid.UUID(raw_user_id), None, None
        except ValueError:
            return None, {"error": "Invalid user_id format"}, 400

    return None, {"error": "Invalid user_id type"}, 400


def _load_tag_for_user(user_id: uuid.UUID, raw_tag_id: str | None):
    """
    Validate and load tag for a given user.

    Returns:
      (tag: Tag | None, error_body: dict | None, status: int | None)

    Rules:
      - if raw_tag_id is empty -> (None, None, None)
      - tag must exist
      - tag must belong to the same user
    """
    if not raw_tag_id:
        return None, None, None

    try:
        tag_uuid = uuid.UUID(raw_tag_id)
    except ValueError:
        return None, {"error": "Invalid tag_id format"}, 400

    tag = db.session.get(Tag, tag_uuid)
    if not tag:
        return None, {"error": "Tag not found"}, 404

    if tag.user_id != user_id:
        return None, {"error": "Tag does not belong to this user"}, 403

    return tag, None, None


def _parse_account_id(raw_account_id):
    if not raw_account_id:
        return None, {"error": "Missing account_id"}, 400

    if isinstance(raw_account_id, uuid.UUID):
        return raw_account_id, None, None

    if isinstance(raw_account_id, str):
        try:
            return uuid.UUID(raw_account_id), None, None
        except ValueError:
            return None, {"error": "Invalid account_id format"}, 400

    return None, {"error": "Invalid account_id type"}, 400


def _ensure_account_membership(user_id: uuid.UUID, account_id: uuid.UUID):
    membership = (
        db.session.query(AccountMember)
        .filter(
            AccountMember.user_id == user_id,
            AccountMember.account_id == account_id,
        )
        .first()
    )
    if membership is None:
        return {"error": "User is not a member of this account"}, 403
    return None


def _resolve_account_for_user(
    user_id: uuid.UUID,
    raw_account_id: str | uuid.UUID | None,
):
    if raw_account_id:
        account_id, err, status = _parse_account_id(raw_account_id)
        if err:
            return None, err, status
        membership_error = _ensure_account_membership(user_id, account_id)
        if membership_error:
            return None, membership_error, 403
        return account_id, None, None

    default_membership = (
        db.session.query(AccountMember)
        .filter(AccountMember.user_id == user_id)
        .order_by(AccountMember.created_at.asc())
        .first()
    )
    if default_membership is None:
        return None, {"error": f"Missing account_id and user has no account membership"}, 400

    return default_membership.account_id, None, None



def create_receipt(data: dict):
    try:
        # user_id
        user_id, err, status = _parse_user_id(data.get("user_id"))
        if err:
            return err, status
        account_id, err, status = _resolve_account_for_user(
            user_id,
            data.get("account_id") or data.get("accountId")
        )
        if err:
            return err, status

        # tag (optional, but must belong to user)
        tag, err, status = _load_tag_for_user(user_id, data.get("tag_id"))
        if err:
            return err, status

        # description (required)
        description = (data.get("description") or "").strip()
        if not description:
            return {"error": "Missing description"}, 400

        # issue_date
        issue_date = None
        if data.get("issue_date"):
            try:
                issue_date = date.fromisoformat(data["issue_date"])
            except ValueError:
                return {"error": "Invalid issue_date format, expected YYYY-MM-DD"}, 400

        receipt = Receipt(
            user_id=user_id,
            account_id=account_id,
            tag=tag,
            description=description,
            issue_date=issue_date,
            total_amount=data.get("total_amount") or 0.0,
            external_uid=data.get("external_uid"),
            extra_metadata=data.get("extra_metadata")
        )

        db.session.add(receipt)

        # Update tag usage & type if tag is present
        if tag is not None:
            tags_service.register_tag_assigned(tag)

        db.session.commit()

        return {"id": str(receipt.id), "message": "Receipt created successfully"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def get_receipt_by_id(receipt_id: uuid.UUID):
    receipt = db.session.get(Receipt, receipt_id)
    if not receipt:
        return {"error": "Receipt not found"}, 404

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
        "created_at": receipt.created_at.isoformat() if receipt.created_at else None
    }, 200


def update_receipt(receipt_id: uuid.UUID, data: dict):
    try:
        receipt = db.session.get(Receipt, receipt_id)
        if not receipt:
            return {"error": "Receipt not found"}, 404

        # Track old tag for proper counter/type updates
        old_tag = receipt.tag
        new_tag = old_tag

        # Tag update
        if "tag_id" in data:
            raw_tag_id = data["tag_id"]
            if raw_tag_id:
                # tag must belong to the same user as receipt
                tag, err, status = _load_tag_for_user(receipt.user_id, raw_tag_id)
                if err:
                    return err, status
                new_tag = tag
            else:
                new_tag = None

        # Apply tag change (if any)
        if new_tag is not old_tag:
            # detach old tag
            if old_tag is not None:
                # remove relationship first
                receipt.tag = None
                tags_service.register_tag_unassigned(old_tag)

            # attach new tag
            if new_tag is not None:
                receipt.tag = new_tag
                tags_service.register_tag_assigned(new_tag)

        # description
        if "description" in data:
            desc = (data["description"] or "").strip()
            if not desc:
                return {"error": "Description cannot be empty"}, 400
            receipt.description = desc

        # issue_date
        if "issue_date" in data:
            receipt.issue_date = date.fromisoformat(data["issue_date"])
        if "account_id" in data:
            new_account_id, err, status = _parse_account_id(data["account_id"])
            if err:
                return err, status
            membership_error = _ensure_account_membership(receipt.user_id, new_account_id)
            if membership_error:
                return membership_error, 403
            receipt.account_id = new_account_id
        if "total_amount" in data:
            receipt.total_amount = float(data["total_amount"])
        if "external_uid" in data:
            receipt.external_uid = data["external_uid"]
        if "extra_metadata" in data:
            receipt.extra_metadata = data["extra_metadata"]

        db.session.commit()

        return {
            "id": str(receipt.id),
            "message": "Receipt updated successfully"
        }, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def delete_receipt(receipt_id: uuid.UUID):
    receipt = db.session.get(Receipt, receipt_id)
    if not receipt:
        return {"error": "Receipt not found"}, 404

    try:
        tag = receipt.tag

        db.session.delete(receipt)

        # If the tag was linked, adjust its counter/type
        if tag is not None:
            tags_service.register_tag_unassigned(tag)

        db.session.commit()
        return {"message": "Receipt deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def import_receipt_from_ekasa(
    receipt_id: str,
    user_id: str,
    account_id: str | None = None,
):
    """Fetch receipt data from eKasa API and store it in local DB."""
    try:
        ekasa_data = ekasa_service.fetch_receipt_data(receipt_id)
        if "error" in ekasa_data:
            return ekasa_data, 400

        r = ekasa_data["receipt"]
        org_data = r.get("organization")

        issue_date = datetime.strptime(r["issueDate"], "%d.%m.%Y %H:%M:%S").date()
        total_price = float(r.get("totalPrice", 0))

        user_uuid, err, status = _parse_user_id(user_id)
        if err:
            return err, status
        account_uuid, err, status = _resolve_account_for_user(user_uuid, account_id)
        if err:
            return err, status

        tag = None
        if org_data:
            # find/create tag for this user based on organization
            tag = tags_service.find_or_create_tag_from_ekasa(user_uuid, org_data)

        description = (
            org_data.get("name")
            if org_data and org_data.get("name")
            else "eKasa receipt"
        )

        receipt = Receipt(
            user_id=user_uuid,
            account_id=account_uuid,
            tag=tag,
            description=description,
            issue_date=issue_date,
            total_amount=total_price,
            external_uid=r.get("receiptId"),
            extra_metadata={
                "ico": r.get("ico"),
                "dic": r.get("dic"),
                "okp": r.get("okp"),
                "unit": r.get("unit", {}),
            },
        )

        db.session.add(receipt)

        # Tag assigned as EXPENSE (receipt)
        if tag is not None:
            tags_service.register_tag_assigned(tag)

        # Items (eKasa can return items=null)
        items = r.get("items") or []  # None -> []
        if not isinstance(items, list):
            items = []

        for i in items:
            item = ReceiptItem(
                receipt=receipt,
                user_id=user_uuid,
                name=(i.get("name") or "").strip(),
                quantity=Decimal(str(i.get("quantity", 1))),
                unit_price=Decimal(str(i.get("price", 0))),
                total_price=Decimal(str(i.get("price", 0))),
                extra_metadata={
                    "vatRate": i.get("vatRate"),
                    "itemType": i.get("itemType"),
                },
            )
            db.session.add(item)

        db.session.commit()

        return {
            "message": "Receipt imported successfully",
            "tag": tag.name if tag else None,
            "tag_id": tag.id if tag else None,
            "receipt_id": str(receipt.id),
            "total_items": len(items),
        }, 201

    except Exception as e:
        db.session.rollback()
        return {"error": f"Import failed: {str(e)}"}, 400

def get_ekasa_items(
    year: int | None = None,
    month: int | None = None,
    user_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
):
    """
    Return eKasa receipt items grouped under their receipt (check) for a given month/year.

    Rules:
      - year and month must be provided together (same as incomes/receipts filters)
      - month must be 1..12
      - only eKasa-imported receipts are included (Receipt.external_uid != null)
      - optional user_id filter
    """
    # month/year validation (same messages as other endpoints)
    if (year is None) ^ (month is None):
        return {"error": "Both year and month must be provided together"}, 400

    start = end = None
    if year is not None and month is not None:
        if month < 1 or month > 12:
            return {"error": "Month must be between 1 and 12"}, 400

        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    query = (
        db.session.query(Receipt)
        .options(
            joinedload(Receipt.items),
            joinedload(Receipt.tag),
            joinedload(Receipt.account),
        )
        .filter(Receipt.external_uid.isnot(None))  # eKasa-import marker
    )

    # optional date filter
    if start is not None and end is not None:
        query = query.filter(
            Receipt.issue_date >= start,
            Receipt.issue_date < end,
        )

    # optional user filter
    if user_id is not None:
        query = query.filter(Receipt.user_id == user_id)
    if account_id is not None:
        query = query.filter(Receipt.account_id == account_id)

    receipts = query.order_by(Receipt.issue_date.asc(), Receipt.created_at.asc()).all()

    checks = []
    total_items = 0

    for r in receipts:
        items = []
        for it in (r.items or []):
            items.append({
                "id": str(it.id),
                "name": it.name,
                "quantity": float(it.quantity) if it.quantity is not None else None,
                "unit_price": float(it.unit_price) if it.unit_price is not None else None,
                "total_price": float(it.total_price) if it.total_price is not None else None,
                "category_id": str(it.category_id) if it.category_id else None,
                "extra_metadata": it.extra_metadata,
            })

        total_items += len(items)

        checks.append({
            "receipt_id": str(r.id),
            "external_uid": r.external_uid,  # eKasa receiptId
            "issue_date": r.issue_date.isoformat() if r.issue_date else None,
            "description": r.description,
            "currency": _receipt_currency(r),
            "total_amount": float(r.total_amount) if r.total_amount is not None else None,
            "tag": r.tag.name if r.tag else None,
            "tag_id": str(r.tag_id) if r.tag_id else None,
            "user_id": str(r.user_id),
            "account_id": str(r.account_id),
            "items": items,
        })

    return {
        "success": True,
        "checks": checks,
        "total_checks": len(checks),
        "total_items": total_items,
    }, 200
