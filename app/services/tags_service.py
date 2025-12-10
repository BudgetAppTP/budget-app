# app/services/tags_service.py

from __future__ import annotations

import uuid

from app.extensions import db
from app.models import Tag
from app.models.tag import TagType


def get_or_create_user_tag(user_id: uuid.UUID, name: str) -> Tag:
    """
    Find a tag for a given user by name or create a new one.

    Tags are user-specific:
      - uniqueness is enforced per user (user_id + name).
    """
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValueError("Tag name cannot be empty")

    tag = (
        db.session.query(Tag)
        .filter(Tag.user_id == user_id, Tag.name == clean_name)
        .first()
    )
    if tag:
        return tag

    tag = Tag(
        user_id=user_id,
        name=clean_name,
        # type is initially None; it will be inferred by update_type()
        type=None,
        counter=0,
    )
    db.session.add(tag)
    db.session.flush()
    return tag


def register_tag_assigned(tag: Tag) -> None:
    """
    Call this when the tag is assigned to an Income or Receipt.

    - increments usage counter
    - updates tag type based on current relationships
    """
    if tag is None:
        return

    tag.increment_counter()
    tag.update_type()


def register_tag_unassigned(tag: Tag) -> None:
    """
    Call this when the tag is removed from an Income or Receipt.

    - decrements usage counter (but not below 0)
    - updates tag type based on current relationships
    """
    if tag is None:
        return

    tag.decrement_counter()
    tag.update_type()


def find_or_create_tag_from_ekasa(user_id: uuid.UUID, data: dict) -> Tag | None:
    """
    Find or create a tag for the given user based on eKasa organization data.

    - uses organization name as tag name
    - does NOT increment counter here
      (counter and type are handled when the tag is actually assigned to a receipt)
    """
    name = data.get("name")
    if not name:
        return None

    tag = (
        db.session.query(Tag)
        .filter(Tag.user_id == user_id, Tag.name == name)
        .first()
    )
    if tag:
        return tag

    # Initially type=None; when we assign it to a Receipt,
    # register_tag_assigned() + update_type() will set it to EXPENSE.
    tag = Tag(
        user_id=user_id,
        name=name,
        type=None,
        counter=0,
    )
    db.session.add(tag)
    db.session.flush()
    return tag
