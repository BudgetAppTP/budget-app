from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .savings_fund import SavingsFund
    from .user import User


class Goal(Base):
    """Represents a savings goal owned by a user inside a savings fund.

    Attributes:
        id (uuid.UUID): Unique identifier for the goal.
        user_id (uuid.UUID): Foreign key referencing the user who owns this goal.
        savings_fund_id (uuid.UUID): Foreign key referencing the savings fund this goal belongs to.
        target_amount (Decimal): Target amount to reach for this goal.
        current_amount (Decimal): Current accumulated amount toward the target.
        is_completed (bool): Indicates whether the goal has already been completed.

    Relationships:
        user (User): Many-to-One relationship.
            The user who owns this goal.

        savings_fund (SavingsFund): Many-to-One relationship.
            The savings fund that tracks this goal.
    """

    __tablename__ = 'goals'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    savings_fund_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('savings_funds.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal('0.00'),
        server_default='0'
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default='0'
    )

    """ Relationships """
    user: Mapped['User'] = relationship(
        'User', back_populates='goals'
    )
    savings_fund: Mapped['SavingsFund'] = relationship(
        'SavingsFund', back_populates='goals'
    )
