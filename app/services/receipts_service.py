import uuid
from decimal import Decimal

from app.extensions import db
from app.models import Receipt, Tag, ReceiptItem
from datetime import date, datetime

from app.services import tags_service, ekasa_service


def get_all_receipts(year: int | None = None, month: int | None = None):
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
    query = db.session.query(Receipt)

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
            "currency": r.currency,
            "total_amount": float(r.total_amount) if r.total_amount is not None else None,
            "extra_metadata": r.extra_metadata,
            "user_id": str(r.user_id),
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



def create_receipt(data: dict):
    try:
        # user_id
        user_id, err, status = _parse_user_id(data.get("user_id"))
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
            tag=tag,
            description=description,
            issue_date=issue_date,
            currency=data.get("currency", "EUR"),
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
        "currency": receipt.currency,
        "total_amount": float(receipt.total_amount) if receipt.total_amount is not None else None,
        "extra_metadata": receipt.extra_metadata,
        "user_id": str(receipt.user_id),
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
        if "currency" in data:
            receipt.currency = data["currency"]
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


def import_receipt_from_ekasa(receipt_id: str, user_id: str):
    """Fetch receipt data from eKasa API and store it in local DB."""
    try:
        ekasa_data = ekasa_service.fetch_receipt_data(receipt_id)
        if "error" in ekasa_data:
            return ekasa_data, 400

        r = ekasa_data["receipt"]
        org_data = r.get("organization")

        issue_date = datetime.strptime(r["issueDate"], "%d.%m.%Y %H:%M:%S").date()
        total_price = float(r.get("totalPrice", 0))

        user_uuid = uuid.UUID(user_id)

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
            tag=tag,
            description=description,
            issue_date=issue_date,
            currency="EUR",
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