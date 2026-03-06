import uuid
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models import Goal, SavingsFund


def compute_unused_amount(fund_id: uuid.UUID) -> Decimal:
    row = (
        db.session.query(
            SavingsFund.balance,
            func.coalesce(func.sum(Goal.current_amount), 0).label("allocated"),
        )
        .outerjoin(
            Goal,
            (Goal.savings_fund_id == SavingsFund.id) & Goal.is_completed.is_(False),
        )
        .filter(SavingsFund.id == fund_id)
        .group_by(SavingsFund.id)
        .first()
    )
    if row is None:
        return Decimal("0.00")
    balance, allocated = row
    return Decimal(balance) - Decimal(allocated)
