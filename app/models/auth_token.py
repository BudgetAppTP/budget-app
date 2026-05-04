"""
AuthToken model

This model stores opaque authentication tokens issued to users upon
successful login. Each token references the user that owns it and has
an explicit expiration time. Tokens can be revoked by deleting them or
by updating the `expires_at` column to a past timestamp. New tokens are
generated as random strings to avoid any correlation between sessions.

Fields:
    id (UUID): Primary key for the token record.
    user_id (UUID): Foreign key referencing the owning user.
    token (str): Opaque random token string.
    created_at (datetime): Timestamp when the token was created.
    expires_at (datetime): Timestamp when the token expires.

Relationships:
    user (User): Backreference to the associated user.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # define relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="auth_tokens")

    def is_expired(self) -> bool:
        from datetime import datetime as _dt
        ea = self.expires_at.replace(tzinfo=None) if self.expires_at.tzinfo else self.expires_at
        return _dt.utcnow() >= ea

    def __repr__(self) -> str:
        return f"<AuthToken id={self.id} user_id={self.user_id} expires_at={self.expires_at.isoformat()}>"