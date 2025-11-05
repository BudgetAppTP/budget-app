from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.utils.types import JSONType

if TYPE_CHECKING:
    from .user import User


class Income(Base):
    """Represents an income record associated with a user.

    Attributes:
        id (uuid.UUID): Unique identifier for the income record.
        user_id (uuid.UUID): Foreign key referencing the user who owns this income.
        amount (Decimal): The amount of income received.
        income_date (date): The date the income was received.
        source (str | None): Optional description or source of the income.
        extra_metadata (dict | None): Optional JSON field containing additional metadata.

    Relationships:
        user (User): Many-to-One relationship.
            The user associated with this income record. Each user can have multiple income entries.
    """
    __tablename__ = 'incomes'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    income_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)

    """ Relationships """
    user: Mapped["User"] = relationship("User", back_populates="incomes")

    def __repr__(self) -> str:
        return f"<Income {self.amount} user_id={self.user_id} from {self.source}>"
