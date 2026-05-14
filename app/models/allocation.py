from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .account import Account


class Allocation(Base):
    """Represents a transfer allocation between two accounts.

    In current business rules, allocations are created from the user's main
    account to a savings fund account. Undo operation removes the allocation row
    and returns money back to the source account.

    Attributes:
        id (uuid.UUID): Unique identifier for the allocation row.
        allocation_date (date): Server-side date when the allocation was created.
        amount (Decimal): Allocated amount moved from source to target account.
        source_account_id (uuid.UUID): Foreign key referencing source account.
        target_account_id (uuid.UUID): Foreign key referencing target account.

    Relationships:
        source_account (Account): Many-to-One relationship.
            The account from which money is allocated.

        target_account (Account): Many-to-One relationship.
            The account that receives allocated money.
    """

    __tablename__ = "allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    allocation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        server_default=func.current_date(),
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    source_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    """ Relationships """
    source_account: Mapped["Account"] = relationship(
        "Account",
        foreign_keys=[source_account_id],
        back_populates="outgoing_allocations",
    )
    target_account: Mapped["Account"] = relationship(
        "Account",
        foreign_keys=[target_account_id],
        back_populates="incoming_allocations",
    )
