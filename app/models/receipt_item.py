import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.utils.types import JSONType


class ReceiptItem(Base):
    """Represents an individual item listed on a purchase receipt.

    Each receipt item belongs to a single receipt and may optionally
    be categorized.

    Attributes:
        id (uuid.UUID): Unique identifier for the receipt item.
        receipt_id (uuid.UUID): Foreign key referencing the associated receipt.
        user_id (uuid.UUID): Foreign key referencing the associated user.
        category_id (uuid.UUID | None): Optional foreign key referencing a category.
        name (str): The name of the item.
        quantity (Decimal): The quantity of the item purchased (default: 1).
        unit_price (Decimal): The price per unit of the item.
        total_price (Decimal): The total price for the item (quantity * unit price).
        extra_metadata (dict | None): Optional JSON field for additional details.

    Relationships:
        user (User): Many-to-One relationship.
            The user who owns this item. Each user can have multiple items across receipts.
        category (Category | None): Many-to-One relationship (optional).
            The category assigned to this item. May be null if uncategorized.
        receipt (Receipt): Many-to-One relationship.
            The receipt this item belongs to. Each receipt can contain multiple items.
    """
    __tablename__ = 'receipt_items'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('receipts.id'),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('categories.id'),
        index=True,
        nullable=True
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONType(), nullable=True)

    """ Relationships """
    user: Mapped["User"] = relationship(
        'User', back_populates="receipt_items"
    )

    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="receipt_items"
    )

    receipt: Mapped["Receipt"] = relationship(
        'Receipt', back_populates='items'
    )

    def __repr__(self) -> str:
        return f"<ReceiptItem {self.name} total_price={self.total_price} user_id={self.user_id}>"
