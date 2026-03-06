import uuid
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models import AccountMember, Goal, SavingsFund
from app.services.errors import BadRequestError, NotFoundError
from app.services.funds_balance_service import compute_unused_amount
from app.services.responses import CreatedResult, OkResult


def _to_decimal(value, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise BadRequestError(f"{field_name} must be a decimal number")


def _serialize_goal(goal: Goal) -> dict:
    return {
        "id": str(goal.id),
        "user_id": str(goal.user_id),
        "savings_fund_id": str(goal.savings_fund_id),
        "target_amount": float(goal.target_amount),
        "current_amount": float(goal.current_amount),
        "is_completed": bool(goal.is_completed),
    }


def _fund_for_user(user_id: uuid.UUID, fund_id: uuid.UUID):
    return (
        db.session.query(SavingsFund)
        .join(AccountMember, AccountMember.account_id == SavingsFund.id)
        .filter(
            SavingsFund.id == fund_id,
            AccountMember.user_id == user_id,
        )
        .first()
    )


def _goal_query_for_user(user_id: uuid.UUID):
    return (
        db.session.query(Goal)
        .join(SavingsFund, SavingsFund.id == Goal.savings_fund_id)
        .join(AccountMember, AccountMember.account_id == SavingsFund.id)
        .filter(
            Goal.user_id == user_id,
            AccountMember.user_id == user_id,
        )
    )


def _get_goal_for_user(user_id: uuid.UUID, goal_id: uuid.UUID, lock: bool = False):
    query = _goal_query_for_user(user_id).filter(Goal.id == goal_id)
    if lock:
        query = query.with_for_update()
    goal = query.first()
    if goal is None:
        raise NotFoundError("Goal not found")
    return goal


def _get_locked_fund(fund_id: uuid.UUID):
    fund = (
        db.session.query(SavingsFund)
        .filter(SavingsFund.id == fund_id)
        .with_for_update()
        .first()
    )
    if fund is None:
        raise NotFoundError("Savings fund not found")
    return fund


def list_goals(user_id: uuid.UUID, savings_fund_id: uuid.UUID | None = None):
    query = _goal_query_for_user(user_id)
    if savings_fund_id is not None:
        query = query.filter(Goal.savings_fund_id == savings_fund_id)

    goals = query.order_by(Goal.id.asc()).all()
    items = [_serialize_goal(goal) for goal in goals]
    return OkResult({"items": items, "count": len(items)})


def create_goal(user_id: uuid.UUID, data: dict):
    raw_fund_id = data.get("savings_fund_id")
    if not raw_fund_id:
        raise BadRequestError("Missing savings_fund_id")

    try:
        fund_id = uuid.UUID(str(raw_fund_id))
    except ValueError:
        raise BadRequestError("Invalid savings_fund_id format")

    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Savings fund not found")

    target_amount = _to_decimal(data.get("target_amount"), "target_amount")

    if target_amount <= 0:
        raise BadRequestError("target_amount must be greater than 0")

    goal = Goal(
        user_id=user_id,
        savings_fund_id=fund_id,
        target_amount=target_amount,
        current_amount=Decimal("0.00"),
        is_completed=False,
    )
    db.session.add(goal)
    db.session.commit()
    return CreatedResult(_serialize_goal(goal))


def update_goal_target(user_id: uuid.UUID, goal_id: uuid.UUID, data: dict):
    goal = _get_goal_for_user(user_id, goal_id)

    if goal.is_completed:
        raise BadRequestError("Completed goal target cannot be updated")

    if "target_amount" not in data:
        raise BadRequestError("target_amount is required")

    target_amount = _to_decimal(data.get("target_amount"), "target_amount")

    if target_amount < goal.current_amount:
        raise BadRequestError("target_amount cannot be lower than current_amount")
    if target_amount <= 0:
        raise BadRequestError("target_amount must be greater than 0")

    goal.target_amount = target_amount
    db.session.commit()
    return OkResult(_serialize_goal(goal))


def adjust_goal_allocation(user_id: uuid.UUID, goal_id: uuid.UUID, delta_amount):
    goal = _get_goal_for_user(user_id, goal_id, lock=True)

    if goal.is_completed:
        raise BadRequestError("Cannot allocate on a completed goal")

    delta = _to_decimal(delta_amount, "delta_amount")

    new_amount = Decimal(goal.current_amount) + delta
    if new_amount < 0:
        raise BadRequestError("Goal allocation cannot be negative")
    if new_amount > Decimal(goal.target_amount):
        raise BadRequestError("Goal allocation cannot exceed target_amount")
    if delta > 0:
        # Ensure we do not reserve more than the fund can currently cover.
        unused_amount = compute_unused_amount(goal.savings_fund_id)
        if delta > unused_amount:
            raise BadRequestError("Insufficient unallocated savings fund balance")

    goal.current_amount = new_amount
    db.session.commit()
    return OkResult(_serialize_goal(goal))


def complete_goal(user_id: uuid.UUID, goal_id: uuid.UUID):
    goal = _get_goal_for_user(user_id, goal_id, lock=True)
    if goal.is_completed:
        raise BadRequestError("Goal is already completed")
    if Decimal(goal.current_amount) < Decimal(goal.target_amount):
        raise BadRequestError("Cannot complete goal before reaching target_amount")

    fund = _get_locked_fund(goal.savings_fund_id)

    if Decimal(fund.balance) < Decimal(goal.target_amount):
        raise BadRequestError("Savings fund balance is insufficient")

    fund.balance = Decimal(fund.balance) - Decimal(goal.target_amount)
    goal.is_completed = True
    db.session.commit()
    return OkResult(_serialize_goal(goal))


def reopen_goal(user_id: uuid.UUID, goal_id: uuid.UUID):
    goal = _get_goal_for_user(user_id, goal_id, lock=True)
    if not goal.is_completed:
        raise BadRequestError("Goal is not completed")

    fund = _get_locked_fund(goal.savings_fund_id)

    fund.balance = Decimal(fund.balance) + Decimal(goal.target_amount)
    goal.is_completed = False
    db.session.commit()
    return OkResult(_serialize_goal(goal))


def delete_goal(user_id: uuid.UUID, goal_id: uuid.UUID):
    goal = _get_goal_for_user(user_id, goal_id)
    if goal.is_completed:
        raise BadRequestError("Completed goal cannot be deleted")
    if Decimal(goal.current_amount) != Decimal("0"):
        raise BadRequestError("Only zero-allocated goals can be deleted")

    db.session.delete(goal)
    db.session.commit()
    return OkResult({"id": str(goal_id)})
