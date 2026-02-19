from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Text, Enum, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from app.utils.types import TagType

if TYPE_CHECKING:
    from .receipt import Receipt
    from .income import Income
    from .user import User


class Tag(Base):
    """Represents a tag for categorizing transactions.

    Tags are user-specific. Each user can have their own tags,
    and the same tag name can exist for different users.

    Attributes:
        id (uuid.UUID): Unique identifier for the tag.
        user_id (uuid.UUID): Foreign key to the user who owns this tag.
        name (str): The tag name (unique per user).
        type (TagType): Type of tag (INCOME, EXPENSE, or BOTH).
            Auto-detected based on relationships.
        counter (int): Usage counter. Increments when tag is assigned,
            decrements when unassigned. Defaults to 0.

    Relationships:
        user (User): Many-to-One relationship.
            The user who owns this tag.
        receipts (list[Receipt]): One-to-Many relationship.
            All receipts associated with this tag.
        incomes (list[Income]): One-to-Many relationship.
            All income records associated with this tag.
    """
    __tablename__ = 'tags'
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_tag_name'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    type: Mapped[TagType | None] = mapped_column(
        Enum(TagType),
        nullable=True
    )

    counter: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default='0'
    )

    """ Relationships """
    user: Mapped["User"] = relationship(
        "User", back_populates="tags"
    )

    receipts: Mapped[list["Receipt"]] = relationship(
        "Receipt", back_populates="tag"
    )

    incomes: Mapped[list["Income"]] = relationship(
        "Income", back_populates="tag"
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name} ({self.type}) user_id={self.user_id} counter={self.counter}>"

    def increment_counter(self) -> None:
        """Increment the usage counter by 1."""
        self.counter += 1

    def decrement_counter(self) -> None:
        """Decrement the usage counter by 1, ensuring it doesn't go below 0."""
        if self.counter > 0:
            self.counter -= 1

    def update_type(self) -> None:
        """Auto-detect and update tag type based on current relationships.

        Type detection logic:
        - Only receipts exist: TagType.EXPENSE
        - Only incomes exist: TagType.INCOME
        - Both receipts and incomes exist: TagType.BOTH
        - Neither exist: None
        """
        has_receipts = len(self.receipts) > 0
        has_incomes = len(self.incomes) > 0

        if has_receipts and has_incomes:
            self.type = TagType.BOTH
        elif has_receipts:
            self.type = TagType.EXPENSE
        elif has_incomes:
            self.type = TagType.INCOME
        else:
            self.type = None
