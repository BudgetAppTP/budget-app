import uuid
from decimal import Decimal
from sqlite3 import IntegrityError

from app.extensions import db
from app.models import Receipt, ReceiptItem, Organization
from datetime import date, datetime

from app.services import ekasa_service, organizations_service


def get_all_receipts():
    receipts = db.session.query(Receipt).all()

    result = []
    for r in receipts:
        result.append({
            "id": str(r.id),
            "external_uid": r.external_uid,
            "organization": r.organization.name if r.organization else None,
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
        if not user_id:
            return {"error": "Missing user_id"}, 400
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return {"error": "Invalid user_id format"}, 400

        organization_id = data.get("organization_id")
        if organization_id:
            try:
                organization_id = uuid.UUID(organization_id)
            except ValueError:
                return {"error": "Invalid organization_id format"}, 400

            organization = db.session.get(Organization, organization_id)
            if not organization:
                return {"error": "Organization not found"}, 404
        else:
            organization_id = None

        issue_date = None
        if data.get("issue_date"):
            try:
                issue_date = date.fromisoformat(data["issue_date"])
            except ValueError:
                return {"error": "Invalid issue_date format, expected YYYY-MM-DD"}, 400

        receipt = Receipt(
            user_id=user_id,
            organization_id=organization_id,
            issue_date=issue_date,
            currency=data.get("currency", "EUR"),
            total_amount=data.get("total_amount") or 0.0,
            external_uid=data.get("external_uid"),
            extra_metadata=data.get("extra_metadata")
        )

        db.session.add(receipt)
        db.session.commit()

        return {"id": str(receipt.id), "message": "Receipt created successfully"}, 201

    except IntegrityError:
        db.session.rollback()
        return {"error": "Database integrity error (invalid foreign key?)"}, 400
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
        "organization": receipt.organization.name if receipt.organization else None,
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
            if data["organization_id"]:
                try:
                    org_id = uuid.UUID(data["organization_id"])
                except ValueError:
                    return {"error": "Invalid organization_id format"}, 400

                organization = db.session.get(Organization, org_id)
                if not organization:
                    return {"error": "Organization not found"}, 404

                receipt.organization_id = org_id
            else:
                receipt.organization_id = None
        if "issue_date" in data:
            try:
                receipt.issue_date = date.fromisoformat(data["issue_date"])
            except ValueError:
                return {"error": "Invalid issue_date format, expected YYYY-MM-DD"}, 400

        if "currency" in data:
            receipt.currency = data["currency"]

        if "total_amount" in data:
            try:
                receipt.total_amount = float(data["total_amount"])
            except (ValueError, TypeError):
                return {"error": "Invalid total_amount format"}, 400

        if "external_uid" in data:
            receipt.external_uid = data["external_uid"]

        if "extra_metadata" in data:
            receipt.extra_metadata = data["extra_metadata"]

        db.session.commit()
        return {"id": str(receipt.id), "message": "Receipt updated successfully"}, 200

    except IntegrityError:
        db.session.rollback()
        return {"error": "Database integrity error (invalid foreign key?)"}, 400
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

        organization = None
        if org_data:
            organization = organizations_service.find_or_create_organization(org_data)

        receipt = Receipt(
            user_id=uuid.UUID(user_id),
            organization_id=organization.id if organization else None,
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
        db.session.flush()

        for i in r.get("items", []):
            item = ReceiptItem(
                receipt_id=receipt.id,
                user_id=uuid.UUID(user_id),
                name=i.get("name").strip(),
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
            "organization": organization.name if organization else None,
            "organization_id": organization.id if organization else None,
            "receipt_id": str(receipt.id),
            "total_items": len(r.get("items", []))
        }, 201

    except Exception as e:
        db.session.rollback()
        return {"error": f"Import failed: {str(e)}"}, 400