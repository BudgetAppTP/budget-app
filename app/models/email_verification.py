"""
EmailVerification model

Stores transient verification codes used to confirm a user's email
address during registration. A code record is created when a new user
registers and is valid until it expires or is marked as used. Once a
verification code is consumed, the corresponding user account can be
marked as verified. Unused and expired codes may be periodically
deleted or allowed to expire naturally.

Fields:
    id (UUID): Primary key for the verification record.
    user_id (UUID): Foreign key referencing the user being verified.
    code (str): A short verification code sent to the user's email.
    expires_at (datetime): Timestamp when the code expires.
    is_used (bool): Indicates whether the code has been used to verify the user.

Relationships:
    user (User): Backreference to the associated user.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="email_verifications")

    def is_expired(self) -> bool:
        from datetime import datetime as _dt
        return _dt.utcnow() >= self.expires_at

    def __repr__(self) -> str:
        return f"<EmailVerification id={self.id} user_id={self.user_id} code={self.code}>"