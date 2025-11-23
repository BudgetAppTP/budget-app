from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Numeric, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class FinancialTarget(Base):
    """Represents a financial goal or savings target defined by a user.

    This model tracks monthly progress toward a financial target, such as a savings goal
    or investment milestone. A target can be defined either by a fixed amount or
    a percentage from income.

    Attributes:
        id (uuid.UUID): Unique identifier for the financial target.
        user_id (uuid.UUID): Foreign key referencing the user who owns this target.
        title (str): Title or short description of the financial target.
        target_amount (Decimal | None): The desired target amount in the specified currency.
        target_percent (Decimal | None): Optional percentage-based target (e.g., % of income).
        currency (str): ISO currency code for monetary values (default: "EUR").
        current_amount (Decimal): Current progress amount toward the target.
        deadline_date (date | None): Optional deadline date for reaching the target.
        is_completed (bool): Indicates whether the financial target has been reached.
        created_at (datetime): Timestamp when the target was created.
        updated_at (datetime): Timestamp when the target was last updated.

    Relationships:
        user (User): Many-to-One relationship.
            The user who owns this financial target. Each user can have multiple financial targets.
    """
    __tablename__ = 'financial_targets'

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

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    target_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )
    target_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    currency: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default='EUR'
    )

    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )
    deadline_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    """ Relationships """
    user: Mapped["User"] = relationship('User', back_populates='financial_targets')

    def __repr__(self) -> str:
        return f"<FinancialTarget {self.title} user_id={self.user_id}>"
