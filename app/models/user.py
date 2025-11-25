from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .income import Income
    from .receipt import Receipt
    from .financial_target import FinancialTarget
    from .category import Category
    from .receipt_item import ReceiptItem
    from .tag import Tag


class User(Base):
    """Represents a user account in the system.

    Attributes:
        id (uuid.UUID): The unique identifier for the user (primary key).
        username (str): The unique username chosen by the user. Must be 32 characters or fewer.
        email (str): The unique email address of the user, up to 255 characters.
        password_hash (str): The hashed password for authentication.
        created_at (datetime.datetime): The UTC timestamp when the user record was created.

    Relationships:
        incomes (list[Income]): One-to-Many relationship (cascade delete).
            All income records associated with this user.

        receipts (list[Receipt]): One-to-Many relationship (cascade delete).
            All receipts created by this user.

        financial_targets (list[FinancialTarget]): One-to-Many relationship (cascade delete).
            All financial targets defined by this user.

        categories (list[Category]): One-to-Many relationship (cascade delete).
            All custom financial categories created by this user.

        receipt_items (list[ReceiptItem]): One-to-Many relationship (cascade delete).
            All receipt items belonging to this user.

        tags (list[Tag]): One-to-Many relationship (cascade delete).
            All tags created by this user for categorizing transactions.
    """
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    """ Relationships """
    incomes: Mapped[list["Income"]] = relationship(
        "Income", back_populates="user", cascade="all, delete-orphan"
    )

    receipts: Mapped[list["Receipt"]] = relationship(
        "Receipt", back_populates="user", cascade="all, delete-orphan"
    )

    financial_targets: Mapped[list["FinancialTarget"]] = relationship(
        "FinancialTarget", back_populates="user", cascade="all, delete-orphan"
    )

    categories: Mapped[list["Category"]] = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )

    receipt_items: Mapped[list["ReceiptItem"]] = relationship(
        "ReceiptItem", back_populates="user", cascade="all, delete-orphan"
    )

    tags: Mapped[list["Tag"]] = relationship(
        "Tag", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<User#{self.id} {self.username}>'
