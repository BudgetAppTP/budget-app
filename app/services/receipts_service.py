import uuid
from decimal import Decimal

from app.extensions import db
from app.models import Receipt
from datetime import date

def get_all_receipts():
    receipts = db.session.query(Receipt).all()

    result = []
    for r in receipts:
        # Serialize the receipt.  Include both the free‑text merchant name and the
        # organization_id reference so clients can choose which to use.  If
        # organization_id is None, the merchant name alone identifies the seller.
        result.append({
            "id": str(r.id),
            "external_uid": r.external_uid,
            "merchant": r.merchant,
            "organization_id": str(r.organization_id) if r.organization_id else None,
            "issue_date": r.issue_date.isoformat() if r.issue_date else None,
            "currency": r.currency,
            "total_amount": float(r.total_amount) if r.total_amount is not None else None,
            "extra_metadata": r.extra_metadata,
            "user_id": str(r.user_id),
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return result


def create_receipt(data):
    try:
        user_id = data.get("user_id")
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Convert organization_id string to UUID if provided
        organization_id = data.get("organization_id")
        if isinstance(organization_id, str):
            organization_id = uuid.UUID(organization_id)

        receipt = Receipt(
            user_id=user_id,
            organization_id=organization_id,
            merchant=data.get("merchant"),
            issue_date=date.fromisoformat(data["issue_date"]) if data.get("issue_date") else None,
            currency=data.get("currency", "EUR"),
            total_amount=Decimal(str(data.get("total_amount", 0))) if isinstance(data.get("total_amount"), (int, float, str, Decimal)) else Decimal("0"),
            external_uid=data.get("external_uid"),
            extra_metadata=data.get("extra_metadata")
        )

        db.session.add(receipt)
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
        "merchant": receipt.merchant,
        "organization_id": str(receipt.organization_id) if receipt.organization_id else None,
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

        if "organization_id" in data:
            org_id = data["organization_id"]
            if isinstance(org_id, str):
                try:
                    org_id = uuid.UUID(org_id)
                except Exception:
                    org_id = None
            receipt.organization_id = org_id
        if "merchant" in data:
            receipt.merchant = data["merchant"]
        if "issue_date" in data:
            receipt.issue_date = date.fromisoformat(data["issue_date"])
        if "currency" in data:
            receipt.currency = data["currency"]
        if "total_amount" in data:
            # use Decimal for internal storage to preserve cents
            receipt.total_amount = Decimal(str(data["total_amount"]))
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
        db.session.delete(receipt)
        db.session.commit()
        return {"message": "Receipt deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400