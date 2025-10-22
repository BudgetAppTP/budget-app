import uuid
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Numeric, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class FinancialTarget(Base):
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
        Date,nullable=True
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
