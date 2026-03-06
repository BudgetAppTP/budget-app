from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .account import Account, AccountType

if TYPE_CHECKING:
    from .goal import Goal


class SavingsFund(Account):
    """Goal-oriented account extension with a target and monthly contribution."""

    __tablename__ = 'savings_funds'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('accounts.id', ondelete='CASCADE'),
        primary_key=True
    )
    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )
    monthly_contribution: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )

    goals: Mapped[list['Goal']] = relationship(
        'Goal',
        back_populates='savings_fund',
        cascade='all, delete-orphan'
    )

    __mapper_args__ = {
        'polymorphic_identity': AccountType.SAVINGS_FUND,
    }
