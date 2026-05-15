from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .allocation import Allocation
    from .account_member import AccountMember
    from .receipt import Receipt
    from .user import User


@enum.unique
class AccountType(str, enum.Enum):
    ACCOUNT = 'account'
    SAVINGS_FUND = 'savings_fund'


class Account(Base):
    """Represents a financial account in the system.

    Attributes:
        id (uuid.UUID): The unique identifier for the account (primary key).
        name (str): The name of the account, up to 255 characters.
        balance (Decimal): Current account balance.
        currency (str): ISO-like 3-character currency code (e.g. EUR, USD).
        account_type (AccountType): Discriminator used for polymorphic account inheritance.

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
    account_type: Mapped[AccountType] = mapped_column(
        Enum(
            AccountType,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            native_enum=False
        ),
        nullable=False,
        default=AccountType.ACCOUNT,
        server_default=AccountType.ACCOUNT.value,
    )

    """ Relationships """
    memberships: Mapped[list['AccountMember']] = relationship(
        'AccountMember',
        back_populates='account',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    users: Mapped[list['User']] = relationship(
        'User',
        secondary='account_members',
        back_populates='accounts',
        overlaps='account,memberships,user,account_memberships'
    )
    receipts: Mapped[list['Receipt']] = relationship(
        'Receipt',
        back_populates='account',
        passive_deletes=True,
    )
    outgoing_allocations: Mapped[list['Allocation']] = relationship(
        'Allocation',
        foreign_keys='Allocation.source_account_id',
        back_populates='source_account'
    )
    incoming_allocations: Mapped[list['Allocation']] = relationship(
        'Allocation',
        foreign_keys='Allocation.target_account_id',
        back_populates='target_account'
    )

    __mapper_args__ = {
        'polymorphic_identity': AccountType.ACCOUNT,
        'polymorphic_on': account_type,
    }
