import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models import Account, AccountMember, AccountType, Allocation, SavingsFund
from app.services.errors import BadRequestError, NotFoundError
from app.services.responses import CreatedResult, OkResult


def _to_decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise BadRequestError(f"{field_name} must be a decimal number")


def _serialize_allocation(allocation: Allocation) -> dict:
    return {
        "id": str(allocation.id),
        "allocation_date": allocation.allocation_date.isoformat(),
        "amount": float(allocation.amount),
        "source_account_id": str(allocation.source_account_id),
        "target_account_id": str(allocation.target_account_id),
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


def _main_account_for_user(user_id: uuid.UUID, lock: bool = False) -> Account:
    query = _main_account_query(user_id)
    if lock:
        query = query.with_for_update()
    account = query.first()
    if account is None:
        raise NotFoundError("Main account not found")
    return account


def _fund_for_user(user_id: uuid.UUID, fund_id: uuid.UUID, lock: bool = False) -> SavingsFund:
    query = (
        db.session.query(SavingsFund)
        .join(AccountMember, AccountMember.account_id == SavingsFund.id)
        .filter(
            AccountMember.user_id == user_id,
            SavingsFund.id == fund_id,
            SavingsFund.account_type == AccountType.SAVINGS_FUND,
        )
    )
    if lock:
        query = query.with_for_update()
    fund = query.first()
    if fund is None:
        raise NotFoundError("Savings fund not found")
    return fund


def _ensure_same_currency(source: Account, target: SavingsFund):
    if source.currency != target.currency:
        raise BadRequestError("Allocation is allowed only between accounts with the same currency")


def list_allocations(user_id: uuid.UUID, fund_id: uuid.UUID):
    fund = _fund_for_user(user_id, fund_id)

    allocations = (
        db.session.query(Allocation)
        .filter(Allocation.target_account_id == fund.id)
        .order_by(Allocation.allocation_date.desc(), Allocation.id.desc())
        .all()
    )
    items = [_serialize_allocation(a) for a in allocations]
    return OkResult({"items": items, "count": len(items)})


def create_allocation(user_id: uuid.UUID, fund_id: uuid.UUID, data: dict):
    main_account = _main_account_for_user(user_id, lock=True)
    fund = _fund_for_user(user_id, fund_id, lock=True)
    _ensure_same_currency(main_account, fund)

    amount = _to_decimal(data.get("amount"), "amount")
    if amount <= 0:
        raise BadRequestError("amount must be greater than 0")
    if Decimal(main_account.balance) < amount:
        raise BadRequestError("Insufficient main account balance")

    main_account.balance = Decimal(main_account.balance) - amount
    fund.balance = Decimal(fund.balance) + amount

    allocation = Allocation(
        allocation_date=date.today(),
        amount=amount,
        source_account_id=main_account.id,
        target_account_id=fund.id,
    )
    db.session.add(allocation)
    db.session.commit()
    return CreatedResult(_serialize_allocation(allocation))


def undo_allocation(user_id: uuid.UUID, fund_id: uuid.UUID, allocation_id: uuid.UUID):
    main_account = _main_account_for_user(user_id, lock=True)
    fund = _fund_for_user(user_id, fund_id, lock=True)

    allocation = (
        db.session.query(Allocation)
        .filter(
            Allocation.id == allocation_id,
            Allocation.source_account_id == main_account.id,
            Allocation.target_account_id == fund.id,
        )
        .with_for_update()
        .first()
    )
    if allocation is None:
        raise NotFoundError("Allocation not found")

    amount = Decimal(allocation.amount)
    if Decimal(fund.balance) < amount:
        raise BadRequestError("Savings fund balance is insufficient to undo allocation")

    fund.balance = Decimal(fund.balance) - amount
    main_account.balance = Decimal(main_account.balance) + amount
    db.session.delete(allocation)
    db.session.commit()
    return OkResult({"id": str(allocation_id)})
