from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .account import Account
    from .user import User


class AccountMember(Base):
    """Association model linking users and accounts (many-to-many)."""

    __tablename__ = 'account_members'
    __table_args__ = (
        UniqueConstraint('user_id', 'account_id', name='uq_account_members_user_account'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('accounts.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default='owner'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    """ Relationships """
    user: Mapped['User'] = relationship(
        'User', back_populates='account_memberships'
    )
    account: Mapped['Account'] = relationship(
        'Account', back_populates='memberships'
    )
