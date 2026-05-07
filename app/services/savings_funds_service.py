import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import func

from app.core.validators import is_valid_iso4217
from app.extensions import db
from app.models import AccountMember, AccountType, Goal, SavingsFund, Income, Receipt
from app.services.errors import BadRequestError, NotFoundError
from app.services.funds_balance_service import compute_unused_amount
from app.services.responses import CreatedResult, OkResult
from app.models import Account, AccountMember, AccountType, Goal, SavingsFund

def _to_decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise BadRequestError(f"{field_name} must be a decimal number")

def _serialize_fund_public(fund: SavingsFund, unallocated_amount: Decimal) -> dict:
    return {
        "id": str(fund.id),
        "title": fund.name,
        "description": fund.description,
        "current_amount": float(fund.balance),
        "target_amount": float(fund.target_amount) if fund.target_amount is not None else None,
        "monthly_contribution": float(fund.monthly_contribution) if fund.monthly_contribution is not None else None,
        "unallocated_amount": float(unallocated_amount),
        "is_completed": bool(fund.is_completed),
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


def get_savings_summary(user_id: uuid.UUID):
    today = date.today()
    month_start = date(today.year, today.month, 1)

    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)

    income_total = (
        db.session.query(func.coalesce(func.sum(Income.amount), 0))
        .filter(
            Income.user_id == user_id,
            Income.income_date >= month_start,
            Income.income_date < next_month_start,
        )
        .scalar()
    )

    expenses_total = (
        db.session.query(func.coalesce(func.sum(Receipt.total_amount), 0))
        .filter(
            Receipt.user_id == user_id,
            Receipt.issue_date >= month_start,
            Receipt.issue_date < next_month_start,
        )
        .scalar()
    )

    current_balance = Decimal(str(income_total)) - Decimal(str(expenses_total))

    active_goals_sum = (
        db.session.query(
            Goal.savings_fund_id.label("fund_id"),
            func.coalesce(func.sum(Goal.current_amount), 0).label("allocated_amount"),
        )
        .filter(Goal.is_completed.is_(False))
        .group_by(Goal.savings_fund_id)
        .subquery()
    )

    funds_aggregates = (
        db.session.query(
            func.coalesce(func.sum(SavingsFund.balance), 0).label("total_in_funds"),
            func.count(SavingsFund.id).label("funds_count"),
            func.coalesce(
                func.sum(
                    SavingsFund.balance
                    - func.coalesce(active_goals_sum.c.allocated_amount, 0)
                ),
                0,
            ).label("total_unallocated_in_funds"),
        )
        .join(AccountMember, AccountMember.account_id == SavingsFund.id)
        .outerjoin(active_goals_sum, active_goals_sum.c.fund_id == SavingsFund.id)
        .filter(
            AccountMember.user_id == user_id,
            SavingsFund.account_type == AccountType.SAVINGS_FUND,
        )
        .one()
    )

    return OkResult({
        "current_balance": float(current_balance),
        "total_in_funds": float(funds_aggregates.total_in_funds),
        "funds_count": int(funds_aggregates.funds_count),
        "total_unallocated_in_funds": float(funds_aggregates.total_unallocated_in_funds),
    })

def _funds_public_query_for_user(user_id: uuid.UUID):
    active_goals_sum = (
        db.session.query(
            Goal.savings_fund_id.label("fund_id"),
            func.coalesce(func.sum(Goal.current_amount), 0).label("used_amount"),
        )
        .filter(Goal.is_completed.is_(False))
        .group_by(Goal.savings_fund_id)
        .subquery()
    )

    return (
        db.session.query(
            SavingsFund,
            (
                SavingsFund.balance
                - func.coalesce(active_goals_sum.c.used_amount, 0)
            ).label("unallocated_amount"),
        )
        .join(AccountMember, AccountMember.account_id == SavingsFund.id)
        .outerjoin(active_goals_sum, active_goals_sum.c.fund_id == SavingsFund.id)
        .filter(
            AccountMember.user_id == user_id,
            SavingsFund.account_type == AccountType.SAVINGS_FUND,
        )
        .order_by(SavingsFund.name.asc())
    )

def list_public_funds(user_id: uuid.UUID):
    rows = _funds_public_query_for_user(user_id).all()

    items = [
        _serialize_fund_public(fund, unallocated_amount)
        for fund, unallocated_amount in rows
    ]

    return OkResult(items)

def get_public_fund(user_id: uuid.UUID, fund_id: uuid.UUID):
    row = (
        _funds_public_query_for_user(user_id)
        .filter(SavingsFund.id == fund_id)
        .first()
    )

    if row is None:
        raise NotFoundError("Fund not found")

    fund, unallocated_amount = row
    return OkResult(_serialize_fund_public(fund, unallocated_amount))

def update_public_fund(user_id: uuid.UUID, fund_id: uuid.UUID, data: dict):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Fund not found")

    if "title" in data:
        title = str(data.get("title") or "").strip()
        if not title:
            raise BadRequestError("title cannot be empty")
        fund.name = title

    if "description" in data:
        description = str(data.get("description") or "").strip()
        fund.description = description or None

    if "target_amount" in data:
        raw = data.get("target_amount")
        fund.target_amount = _to_decimal(raw, "target_amount") if raw is not None else None

    if "monthly_contribution" in data:
        raw = data.get("monthly_contribution")
        fund.monthly_contribution = (
            _to_decimal(raw, "monthly_contribution")
            if raw is not None
            else None
        )

    db.session.commit()

    return get_public_fund(user_id, fund_id)

def delete_public_fund(user_id: uuid.UUID, fund_id: uuid.UUID):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Fund not found")

    db.session.delete(fund)
    db.session.commit()

    return OkResult({"success": True})


def update_fund_status(user_id: uuid.UUID, fund_id: uuid.UUID, data: dict):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Fund not found")

    if "is_completed" not in data:
        raise BadRequestError("Missing is_completed")

    is_completed = data.get("is_completed")
    if not isinstance(is_completed, bool):
        raise BadRequestError("is_completed must be boolean")

    fund.is_completed = is_completed
    db.session.commit()

    return OkResult({
        "id": str(fund.id),
        "is_completed": fund.is_completed,
    })

def create_public_fund(user_id: uuid.UUID, data: dict, max_savings_funds: int = 10):
    existing = _funds_query_for_user(user_id).count()
    if existing >= max_savings_funds:
        raise BadRequestError(f"Savings funds limit reached ({max_savings_funds})")

    title = str(data.get("title") or "").strip()
    if not title:
        raise BadRequestError("Missing title")

    description = str(data.get("description") or "").strip() or None

    target_amount = data.get("target_amount")
    target_amount = _to_decimal(target_amount, "target_amount") if target_amount is not None else None

    monthly_contribution = data.get("monthly_contribution")
    monthly_contribution = (
        _to_decimal(monthly_contribution, "monthly_contribution")
        if monthly_contribution is not None
        else None
    )

    fund = SavingsFund(
        name=title,
        balance=Decimal("0.00"),
        currency="EUR",
        account_type=AccountType.SAVINGS_FUND,
        target_amount=target_amount,
        monthly_contribution=monthly_contribution,
        description=description,
        is_completed=False,
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

    return CreatedResult(_serialize_fund_public(fund, Decimal("0.00")))

def adjust_balance(user_id: uuid.UUID, fund_id: uuid.UUID, delta_amount):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Fund not found")

    delta = _to_decimal(delta_amount, "delta_amount")

    new_balance = Decimal(fund.balance) + delta
    if new_balance < 0:
        raise BadRequestError("Resulting balance cannot be negative")

    fund.balance = new_balance
    db.session.commit()

    return get_public_fund(user_id, fund_id)