import uuid

from app.extensions import db
from app.models import Receipt
from datetime import date

def get_all_receipts():
    receipts = db.session.query(Receipt).all()

    result = []
    for r in receipts:
        result.append({
            "id": str(r.id),
            "external_uid": r.external_uid,
            "merchant": r.merchant,
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

        receipt = Receipt(
            user_id=user_id,
            merchant=data.get("merchant"),
            issue_date=date.fromisoformat(data["issue_date"]) if data.get("issue_date") else None,
            currency=data.get("currency", "EUR"),
            total_amount=data.get("total_amount") or 0.0,
            external_uid=data.get("external_uid"),
            extra_metadata=data.get("extra_metadata")
        )

        db.session.add(receipt)
        db.session.commit()

        return {"id": str(receipt.id), "message": "Receipt created successfully"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
