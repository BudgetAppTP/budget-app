from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Date, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.utils.types import JSONType

if TYPE_CHECKING:
    from .user import User
    from .organization import Organization


class Income(Base):
    """Represents an income record associated with a user.

    Attributes:
        id (uuid.UUID): Unique identifier for the income record.
        user_id (uuid.UUID): Foreign key referencing the user who owns this income.
        organization_id (uuid.UUID | None): Optional foreign key referencing the organization (income source).
        amount (Decimal): The amount of income received.
        income_date (date): The date the income was received.
        extra_metadata (dict | None): Optional JSON field containing additional metadata.

    Relationships:
        user (User): Many-to-One relationship.
            The user associated with this income record. Each user can have multiple income entries.
        organization (Organization | None): Many-to-One relationship.
            Optional organization associated with this income record.
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
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('organizations.id'),
        nullable=True,
        index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    income_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)

    # Optional free‑text income source.  This allows describing where the income
    # originated (e.g. employer name) without requiring a related Organization
    # entry.  It aligns the API and service layer, which expect a `source`
    # attribute on Income records.
    source: Mapped[str | None] = mapped_column(Text, nullable=True)

    """ Relationships """
    user: Mapped["User"] = relationship("User", back_populates="incomes")

    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="incomes"
    )

    def __repr__(self) -> str:
        return f"<Income {self.amount} user_id={self.user_id} organization_id={self.organization_id}>"
