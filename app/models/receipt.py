from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, Date, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.utils.types import JSONType

if TYPE_CHECKING:
    from .user import User
    from .organization import Organization
    from .receipt_item import ReceiptItem


class Receipt(Base):
    """Represents a purchase receipt.

    Each receipt belongs to a user and may contain multiple receipt items.

    Attributes:
        id (uuid.UUID): Unique identifier for the receipt.
        external_uid (str | None): Optional external identifier used by third-party systems.
        user_id (uuid.UUID): Foreign key referencing the associated user's ID.
        organization_id (uuid.UUID | None): Optional foreign key referencing the organization (merchant).
        issue_date (date): The date the receipt was issued.
        currency (str): The ISO currency code for the receipt amount (default: "EUR").
        total_amount (float): The total monetary amount of the receipt.
        extra_metadata (dict | None): Optional JSON field containing extra metadata.
        created_at (datetime): Timestamp indicating when the record was created.

    Relationships:
        user (User): Many-to-One relationship.
            The user who owns this receipt. Each user may have multiple receipts.
        organization (Organization | None): Many-to-One relationship.
            Optional merchant organization associated with this receipt.
        items (list[ReceiptItem]): One-to-Many relationship.
            The list of receipt items associated with this receipt. Each item
            belongs to exactly one receipt.
    """
    __tablename__ = 'receipts'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    external_uid: Mapped[str | None] = mapped_column(
        Text,
        index=True,
        nullable=True
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

    # Optional merchant name for the receipt.  This free‑text field allows the
    # API to store the seller name directly without always creating an
    # Organization record.  Many endpoints and services expect a `merchant`
    # attribute on Receipt instances; adding this column aligns the model with
    # those expectations.
    merchant: Mapped[str | None] = mapped_column(Text, nullable=True)

    issue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    currency: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default='EUR'
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSONType(),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    """ Relationships """
    user: Mapped["User"] = relationship(
        'User', back_populates='receipts'
    )

    organization: Mapped["Organization | None"] = relationship(
        'Organization', back_populates='receipts'
    )

    items: Mapped[list["ReceiptItem"]] = relationship(
        'ReceiptItem', back_populates='receipt', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<Receipt organization_id={self.organization_id} total_amount={self.total_amount} user_id={self.user_id}>"
