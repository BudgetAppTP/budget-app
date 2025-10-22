import uuid

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    """Represents a user account in the system.

    Attributes:
        id (uuid.UUID): The unique identifier for the user (primary key).
        username (str): The unique username chosen by the user. Must be 32 characters or fewer.
        email (str): The unique email address of the user, up to 255 characters.
        password_hash (str): The hashed password for authentication.
        created_at (datetime.datetime): The UTC timestamp when the user record was created.
    """
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    def __repr__(self):
        return f'<User#{self.pid} {self.username}>'
