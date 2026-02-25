from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .account_member import AccountMember
    from .receipt import Receipt
    from .user import User


class Account(Base):
    """Represents a financial account in the system.

    Attributes:
        id (uuid.UUID): The unique identifier for the account (primary key).
        name (str): The name of the account, up to 255 characters.
        balance (Decimal): Current account balance.
        currency (str): ISO-like 3-character currency code (e.g. EUR, USD).

    Relationships:
        memberships (list[AccountMember]): One-to-Many relationship (cascade delete).
            Association rows linking users to this account.

        users (list[User]): Many-to-Many relationship via AccountMember.
            Users who have access/ownership of this account.

        receipts (list[Receipt]): One-to-Many relationship.
            Receipts linked to this account.
    """
    __tablename__ = 'accounts'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default='0'
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )

    """ Relationships """
    memberships: Mapped[list['AccountMember']] = relationship(
        'AccountMember',
        back_populates='account',
        cascade='all, delete-orphan'
    )
    users: Mapped[list['User']] = relationship(
        'User',
        secondary='account_members',
        back_populates='accounts',
        overlaps='account,memberships,user,account_memberships'
    )
    receipts: Mapped[list['Receipt']] = relationship(
        'Receipt', back_populates='account'
    )
