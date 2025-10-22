import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey, Text, Date, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.utils.types import JSONType


class Receipt(Base):
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

    merchant: Mapped[str] = mapped_column(Text)
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
        'User',
        back_populates='receipts'
    )
    items: Mapped[list["ReceiptItem"]] = relationship(
        'ReceiptItem',
        back_populates='receipt',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f"<Receipt {self.merchant} total_amount={self.total_amount} user_id={self.user_id}>"

