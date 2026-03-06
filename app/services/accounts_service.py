import uuid

from app.extensions import db
from app.models import Account, AccountMember, AccountType
from app.services.errors import BadRequestError, NotFoundError
from app.services.responses import OkResult


def _serialize_account(account: Account) -> dict:
    return {
        "id": str(account.id),
        "name": account.name,
        "balance": float(account.balance),
        "currency": account.currency,
        "account_type": account.account_type.value,
    }


def _main_account_query(user_id: uuid.UUID):
    return (
        db.session.query(Account)
        .join(AccountMember, AccountMember.account_id == Account.id)
        .filter(
            AccountMember.user_id == user_id,
            Account.account_type == AccountType.ACCOUNT,
        )
        .order_by(AccountMember.created_at.asc())
    )


def get_main_account(user_id: uuid.UUID):
    account = _main_account_query(user_id).first()
    if account is None:
        raise NotFoundError("Main account not found")
    return OkResult(_serialize_account(account))


def update_main_account(user_id: uuid.UUID, data: dict):
    account = _main_account_query(user_id).first()
    if account is None:
        raise NotFoundError("Main account not found")

    if "name" in data:
        name = str(data.get("name") or "").strip()
        if not name:
            raise BadRequestError("name cannot be empty")
        account.name = name

    if "currency" in data:
        currency = str(data.get("currency") or "").strip().upper()
        if len(currency) != 3:
            raise BadRequestError("currency must be 3 characters")
        account.currency = currency

    if "balance" in data:
        raise BadRequestError("balance is read-only here")

    db.session.commit()
    return OkResult(_serialize_account(account))
