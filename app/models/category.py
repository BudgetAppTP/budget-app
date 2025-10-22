import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=True,
        index=True
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('categories.id'),
        nullable=True
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Self-referential relationship
    children: Mapped[List["Category"]] = relationship(
        'Category',
        back_populates='parent',
        cascade='all, delete-orphan',
        remote_side=[id]
    )
    parent: Mapped[Optional["Category"]] = relationship(
        'Category',
        back_populates='children',
        remote_side=[id]
    )

    def __repr__(self) -> str:
        return f"<Category {self.name} user_id={self.user_id}>"
