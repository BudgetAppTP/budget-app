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


def _serialize_goal_public(goal: Goal) -> dict:
    return {
        "id": str(goal.id),
        "fund_id": str(goal.savings_fund_id),
        "title": goal.title,
        "description": goal.description,
        "current_amount": float(goal.current_amount),
        "target_amount": float(goal.target_amount),
        "is_completed": bool(goal.is_completed),
    }


def _fund_for_user(user_id: uuid.UUID, fund_id: uuid.UUID) -> SavingsFund | None:
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


def _goal_for_user(user_id: uuid.UUID, goal_id: uuid.UUID, lock: bool = False) -> Goal | None:
    query = _goal_query_for_user(user_id).filter(Goal.id == goal_id)
    if lock:
        query = query.with_for_update()
    return query.first()


def _get_goal_for_user_or_404(user_id: uuid.UUID, goal_id: uuid.UUID, lock: bool = False) -> Goal:
    goal = _goal_for_user(user_id, goal_id, lock=lock)
    if goal is None:
        raise NotFoundError("Goal not found")
    return goal


def list_goals_by_fund(user_id: uuid.UUID, fund_id: uuid.UUID):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Fund not found")

    goals = (
        _goal_query_for_user(user_id)
        .filter(Goal.savings_fund_id == fund_id)
        .order_by(Goal.title.asc(), Goal.id.asc())
        .all()
    )

    items = [_serialize_goal_public(goal) for goal in goals]
    return OkResult(items)


def create_goal(user_id: uuid.UUID, fund_id: uuid.UUID, data: dict):
    fund = _fund_for_user(user_id, fund_id)
    if fund is None:
        raise NotFoundError("Fund not found")

    title = str(data.get("title") or "").strip()
    if not title:
        raise BadRequestError("Missing title")

    description = str(data.get("description") or "").strip() or None

    if "target_amount" not in data:
        raise BadRequestError("Missing target_amount")

    target_amount = _to_decimal(data.get("target_amount"), "target_amount")
    if target_amount <= 0:
        raise BadRequestError("target_amount must be greater than 0")

    goal = Goal(
        user_id=user_id,
        savings_fund_id=fund_id,
        title=title,
        description=description,
        target_amount=target_amount,
        current_amount=Decimal("0.00"),
        is_completed=False,
    )

    db.session.add(goal)
    db.session.commit()

    return CreatedResult(_serialize_goal_public(goal))


def update_goal(user_id: uuid.UUID, goal_id: uuid.UUID, data: dict):
    goal = _get_goal_for_user_or_404(user_id, goal_id)

    if "title" in data:
        title = str(data.get("title") or "").strip()
        if not title:
            raise BadRequestError("title cannot be empty")
        goal.title = title

    if "description" in data:
        description = str(data.get("description") or "").strip()
        goal.description = description or None

    if "target_amount" in data:
        raw_target_amount = data.get("target_amount")
        if raw_target_amount is None:
            raise BadRequestError("target_amount cannot be null")

        target_amount = _to_decimal(raw_target_amount, "target_amount")
        if target_amount <= 0:
            raise BadRequestError("target_amount must be greater than 0")
        if target_amount < Decimal(goal.current_amount):
            raise BadRequestError("target_amount cannot be lower than current_amount")

        goal.target_amount = target_amount

    db.session.commit()
    return OkResult(_serialize_goal_public(goal))


def delete_goal(user_id: uuid.UUID, goal_id: uuid.UUID):
    goal = _get_goal_for_user_or_404(user_id, goal_id)

    db.session.delete(goal)
    db.session.commit()

    return OkResult({"success": True})


def update_goal_status(user_id: uuid.UUID, goal_id: uuid.UUID, data: dict):
    goal = _get_goal_for_user_or_404(user_id, goal_id)

    if "is_completed" not in data:
        raise BadRequestError("Missing is_completed")

    is_completed = data.get("is_completed")
    if not isinstance(is_completed, bool):
        raise BadRequestError("is_completed must be boolean")

    if is_completed and Decimal(goal.current_amount) < Decimal(goal.target_amount):
        raise BadRequestError("Goal cannot be completed before reaching target_amount")

    goal.is_completed = is_completed
    db.session.commit()

    return OkResult({
        "id": str(goal.id),
        "is_completed": goal.is_completed,
    })


def adjust_goal_amount(user_id: uuid.UUID, goal_id: uuid.UUID, delta_amount):
    goal = _get_goal_for_user_or_404(user_id, goal_id, lock=True)

    if goal.is_completed:
        raise BadRequestError("Cannot change amount of a completed goal")

    delta = _to_decimal(delta_amount, "delta_amount")

    new_amount = Decimal(goal.current_amount) + delta
    if new_amount < 0:
        raise BadRequestError("current_amount cannot be negative")
    if new_amount > Decimal(goal.target_amount):
        raise BadRequestError("current_amount cannot exceed target_amount")

    if delta > 0:
        unused_amount = Decimal(str(compute_unused_amount(goal.savings_fund_id)))
        if delta > unused_amount:
            raise BadRequestError("Insufficient unallocated amount in fund")

    goal.current_amount = new_amount
    db.session.commit()

    return OkResult(_serialize_goal_public(goal))