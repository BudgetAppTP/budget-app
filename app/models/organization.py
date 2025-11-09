from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from .base import Base
from app.utils.types import JSONType, OrganizationType

if TYPE_CHECKING:
    from .receipt import Receipt
    from .income import Income


class Organization(Base):
    """Represents a global organization (merchant or income source).

    Organizations are shared across all users. The same organization name
    can appear multiple times with different data (e.g., different addresses).

    Attributes:
        id (uuid.UUID): Unique identifier for the organization.
        name (str): The organization name (not unique).
        type (OrganizationType): Type of organization (MERCHANT, INCOME_SOURCE, or BOTH).
        address (str | None): Optional physical or mailing address.
        website (str | None): Optional website URL.
        contact_info (str | None): Optional contact information (phone, email, etc).
        extra_metadata (dict | None): Optional JSON field containing additional metadata.
        created_at (datetime): Timestamp when the organization was created.

    Relationships:
        receipts (list[Receipt]): One-to-Many relationship.
            All receipts associated with this organization.
        incomes (list[Income]): One-to-Many relationship.
            All income records associated with this organization.
    """
    __tablename__ = 'organizations'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType),
        nullable=False,
        default=OrganizationType.NONE
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    """ Relationships """
    receipts: Mapped[list["Receipt"]] = relationship(
        "Receipt", back_populates="organization"
    )

    incomes: Mapped[list["Income"]] = relationship(
        "Income", back_populates="organization"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name} ({self.type}) address={self.address}>"
