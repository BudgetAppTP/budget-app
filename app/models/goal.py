from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .savings_fund import SavingsFund
    from .user import User


class Goal(Base):
    """Represents a goal tracked within a specific savings fund."""

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

    """ Relationships """
    user: Mapped['User'] = relationship(
        'User', back_populates='goals'
    )
    savings_fund: Mapped['SavingsFund'] = relationship(
        'SavingsFund', back_populates='goals'
    )
