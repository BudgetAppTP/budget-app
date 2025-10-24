import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Category(Base):
    """Represents a category used to organize expences represented by receipt items.

    Categories can be user-specific or shared (if `user_id` is null). They may also
    be hierarchical, allowing categories to have parent and child categories.

    Attributes:
        id (uuid.UUID): Unique identifier for the category.
        user_id (uuid.UUID | None): Optional foreign key referencing the user who owns this category.
            If null, the category may be considered global or shared.
        parent_id (uuid.UUID | None): Optional foreign key referencing the parent category.
        name (str): The name of the category.
        created_at (datetime): Timestamp indicating when the category was created.

    Relationships:
        parent (Category | None): Many-to-One self-referential relationship.
            The parent category of this category, if it exists.
        children (list[Category]): One-to-Many self-referential relationship.
            List of subcategories that belong to this category.
    """
    __tablename__ = 'categories'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=True,
        index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('categories.id'),
        nullable=True
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    """ Relationships """
    # Self-referential relationship
    children: Mapped[List["Category"]] = relationship(
        'Category',
        back_populates='parent',
        cascade='all, delete-orphan',
        remote_side=[id]
    )
    parent: Mapped["Category | None"] = relationship(
        'Category',
        back_populates='children',
        remote_side=[id]
    )

    def __repr__(self) -> str:
        return f"<Category {self.name} user_id={self.user_id}>"
