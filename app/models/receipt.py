from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.utils.types import JSONType

if TYPE_CHECKING:
    from .account import Account
    from .user import User
    from .receipt_item import ReceiptItem
    from .tag import Tag


class Receipt(Base):
    """Represents a purchase receipt.

    Each receipt belongs to a single account, is created by a user,
    and may contain multiple receipt items.

    Attributes:
        id (uuid.UUID): Unique identifier for the receipt.
        external_uid (str | None): Optional external identifier used by third-party systems.
        user_id (uuid.UUID): Foreign key referencing the user who created the receipt.
        account_id (uuid.UUID): Foreign key referencing the associated account.
        tag_id (uuid.UUID | None): Optional foreign key referencing the tag (expense type).
        description (str): A required textual description of the receipt.
        issue_date (date): The date the receipt was issued.
        total_amount (float): The total monetary amount of the receipt.
        extra_metadata (dict | None): Optional JSON field containing extra metadata.
        created_at (datetime): Timestamp indicating when the record was created.

    Relationships:
        user (User): Many-to-One relationship.
            The user who created this receipt.

        account (Account): Many-to-One relationship.
            The account this receipt belongs to.

        tag (Tag | None): Many-to-One relationship.
            Optional tag associated with this receipt.

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
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('accounts.id'),
        nullable=False,
        index=True
    )
    tag_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('tags.id'),
        nullable=True,
        index=True
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    issue_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
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

    account: Mapped["Account"] = relationship(
        'Account', back_populates='receipts'
    )

    tag: Mapped["Tag | None"] = relationship(
        'Tag', back_populates='receipts'
    )

    items: Mapped[list["ReceiptItem"]] = relationship(
        'ReceiptItem', back_populates='receipt', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return (
            f"<Receipt description={self.description!r} "
            f"tag_id={self.tag_id} total_amount={self.total_amount} "
            f"user_id={self.user_id} account_id={self.account_id}>"
        )
