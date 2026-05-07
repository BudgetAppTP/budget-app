from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .account import Account, AccountType

if TYPE_CHECKING:
    from .goal import Goal


class SavingsFund(Account):
    """Represents a specialized account used for savings planning.

    This model extends :class:`Account` using SQLAlchemy polymorphic inheritance
    and adds optional savings-specific targets.

    Attributes:
        id (uuid.UUID): Primary key and foreign key referencing the base account row.
        target_amount (Decimal | None): Optional long-term target amount for the savings fund.
        monthly_contribution (Decimal | None): Optional planned monthly contribution amount.

    Relationships:
        goals (list[Goal]): One-to-Many relationship (cascade delete).
            All goals tracked under this savings fund.
    """

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

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default='0'
    )

    goals: Mapped[list['Goal']] = relationship(
        'Goal',
        back_populates='savings_fund',
        cascade='all, delete-orphan'
    )

    __mapper_args__ = {
        'polymorphic_identity': AccountType.SAVINGS_FUND,
    }
