import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy import func

from app.core.validators import is_valid_iso4217
from app.extensions import db
from app.models import AccountMember, AccountType, Goal, SavingsFund
from app.services.errors import BadRequestError, NotFoundError
from app.services.funds_balance_service import compute_unused_amount
from app.services.responses import CreatedResult, OkResult


def _to_decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise BadRequestError(f"{field_name} must be a decimal number")


def _serialize_fund(fund: SavingsFund, unused_amount: Decimal | None = None) -> dict:
    if unused_amount is None:
        unused_amount = compute_unused_amount(fund.id)
    return {
        "id": str(fund.id),
        "name": fund.name,
        "balance": float(fund.balance),
        "currency": fund.currency,
        "target_amount": float(fund.target_amount) if fund.target_amount is not None else None,
        "monthly_contribution": float(fund.monthly_contribution) if fund.monthly_contribution is not None else None,
        "unused_amount": float(unused_amount),
    }


def _funds_query_for_user(user_id: uuid.UUID):
    return (
        db.session.query(SavingsFund)
        .join(AccountMember, AccountMember.account_id == SavingsFund.id)
        .filter(
            AccountMember.user_id == user_id,
            SavingsFund.account_type == AccountType.SAVINGS_FUND,
        )
    )


def _fund_for_user(user_id: uuid.UUID, fund_id: uuid.UUID) -> SavingsFund | None:
    return _funds_query_for_user(user_id).filter(SavingsFund.id == fund_id).first()


def _funds_with_unused_amount_query_for_user(user_id: uuid.UUID):
    """Return a query yielding (SavingsFund, unused_amount) rows for a user.

    Filters savings funds by account membership, left-joins active goals,
    and computes `unused_amount` as:

        fund.balance - COALESCE(SUM(goal.current_amount), 0)

    per fund.
    """
    return (
        db.session.query(
            SavingsFund,
            (
                SavingsFund.balance
                - func.coalesce(func.sum(Goal.current_amount), 0)
            ).label("unused_amount"),
        )
        .join(AccountMember, AccountMember.account_id == SavingsFund.id)
        .outerjoin(
            Goal,
            (Goal.savings_fund_id == SavingsFund.id) & Goal.is_completed.is_(False),
        )
        .filter(
            AccountMember.user_id == user_id,
            SavingsFund.account_type == AccountType.SAVINGS_FUND,
        )
        .group_by(SavingsFund.id)
        .order_by(SavingsFund.name.asc())
    )


def list_funds(user_id: uuid.UUID):
    rows = _funds_with_unused_amount_query_for_user(user_id).all()
    items = [_serialize_fund(fund, unused_amount) for fund, unused_amount in rows]
    return OkResult({"items": items, "count": len(items)})


def create_fund(user_id: uuid.UUID, data: dict, max_savings_funds: int = 10):
    existing = _funds_query_for_user(user_id).count()
    if existing >= max_savings_funds:
        raise BadRequestError(f"Savings funds limit reached ({max_savings_funds})")

    name = str(data.get("name") or "").strip()
    currency = str(data.get("currency") or "").strip().upper()
    if not name:
        raise BadRequestError("Missing name")
    if not is_valid_iso4217(currency):
        raise BadRequestError("currency must be a valid ISO 4217 code")

    target_amount = data.get("target_amount")
    target_amount = _to_decimal(target_amount, "target_amount") if target_amount is not None else None
    monthly_contribution = data.get("monthly_contribution")
    monthly_contribution = _to_decimal(monthly_contribution, "monthly_contribution") if monthly_contribution is not None else None

    fund = SavingsFund(
        name=name,
        balance=Decimal("0.00"),
        currency=currency,
        account_type=AccountType.SAVINGS_FUND,
        target_amount=target_amount,
        monthly_contribution=monthly_contribution,
    )
    db.session.add(fund)
    db.session.flush()
    db.session.add(
        AccountMember(
            user_id=user_id,
            account_id=fund.id,
            role="owner",
        )
    )
    db.session.commit()
    return CreatedResult(_serialize_fund(fund))


def get_fund(user_id: uuid.UUID, fund_id: uuid.UUID):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Savings fund not found")
    return OkResult(_serialize_fund(fund))


def update_fund(user_id: uuid.UUID, fund_id: uuid.UUID, data: dict):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Savings fund not found")

    if "name" in data:
        name = str(data.get("name") or "").strip()
        if not name:
            raise BadRequestError("name cannot be empty")
        fund.name = name

    if "currency" in data:
        currency = str(data.get("currency") or "").strip().upper()
        if not is_valid_iso4217(currency):
            raise BadRequestError("currency must be a valid ISO 4217 code")
        fund.currency = currency

    if "target_amount" in data:
        raw = data.get("target_amount")
        fund.target_amount = _to_decimal(raw, "target_amount") if raw is not None else None
    if "monthly_contribution" in data:
        raw = data.get("monthly_contribution")
        fund.monthly_contribution = _to_decimal(raw, "monthly_contribution") if raw is not None else None

    db.session.commit()
    return OkResult(_serialize_fund(fund))


def delete_fund(user_id: uuid.UUID, fund_id: uuid.UUID):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Savings fund not found")

    db.session.delete(fund)
    db.session.commit()
    return OkResult({"id": str(fund_id)})


def adjust_balance(user_id: uuid.UUID, fund_id: uuid.UUID, delta_amount):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Savings fund not found")

    delta = _to_decimal(delta_amount, "delta_amount")

    new_balance = Decimal(fund.balance) + delta
    if new_balance < 0:
        raise BadRequestError("Resulting balance cannot be negative")

    fund.balance = new_balance
    db.session.commit()
    return OkResult(_serialize_fund(fund))
