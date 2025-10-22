import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.utils.types import JSONType


class ReceiptItem(Base):
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
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
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
    user: Mapped["User"] = relationship('User')
    category: Mapped[Optional["Category"]]= relationship('Category')
    receipt: Mapped["Receipt"] = relationship('Receipt', back_populates='items')

    def __repr__(self) -> str:
        return f"<ReceiptItem {self.name} total_price={self.total_price} user_id={self.user_id}>"
