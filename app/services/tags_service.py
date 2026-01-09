# app/services/tags_service.py

from __future__ import annotations

import uuid

from app.extensions import db
from app.models import Tag
from app.models.tag import TagType
from typing import List, Dict, Any, Tuple



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


# ---------------------------------------------------------------------------
# Additional tag service operations
#
# These functions expose CRUD-style operations for tags, which are used by
# corresponding API endpoints. They complement the existing helper functions
# above without affecting legacy behavior.

def get_tags_by_type(tag_type: TagType) -> Tuple[Dict[str, Any], int]:
    """
    Retrieve all tags filtered by type.

    Tags whose type matches the requested type are returned. Tags with
    ``TagType.BOTH`` are also included in both income and expense results.

    Args:
        tag_type: The desired tag type (INCOME or EXPENSE).

    Returns:
        A tuple of (payload dict, status). The payload contains a list of
        ``tags`` and a ``count``. Each tag dictionary includes ``id``,
        ``user_id``, ``name``, ``type``, and ``counter``.
    """
    if tag_type not in (TagType.INCOME, TagType.EXPENSE):
        return {"error": "Invalid tag type"}, 400
    tags = db.session.query(Tag).all()
    items: List[Dict[str, Any]] = []
    for t in tags:
        if t.type == tag_type or t.type == TagType.BOTH:
            items.append({
                "id": str(t.id),
                "user_id": str(t.user_id),
                "name": t.name,
                "type": t.type.value if t.type else None,
                "counter": t.counter,
            })
    return {"tags": items, "count": len(items)}, 200


def create_tag(data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Create a new tag for a user.

    The payload must include ``user_id`` and ``name``. Optionally ``type`` may
    be provided as ``"income"``, ``"expense"`` or ``"both"``. If a tag with
    the same name already exists for the user, the existing tag is returned.

    Args:
        data: JSON payload with keys ``user_id`` (str or UUID), ``name`` (str),
              and optional ``type`` (str).

    Returns:
        A tuple of (payload dict, status). On success the payload contains
        ``id`` and a success ``message``.
    """
    import uuid
    try:
        raw_user_id = data.get("user_id")
        if not raw_user_id:
            return {"error": "Missing user_id"}, 400
        try:
            user_uuid = uuid.UUID(str(raw_user_id))
        except Exception:
            return {"error": "Invalid user_id format"}, 400
        name = (data.get("name") or "").strip()
        if not name:
            return {"error": "Tag name cannot be empty"}, 400
        raw_type = data.get("type")
        tag_type = None
        if raw_type is not None:
            try:
                tag_type = TagType(raw_type)
            except ValueError:
                return {"error": "Invalid tag type"}, 400
        tag = get_or_create_user_tag(user_uuid, name)
        if tag_type is not None:
            tag.type = tag_type
        db.session.commit()
        return {"id": str(tag.id), "message": "Tag created successfully"}, 201
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def update_tag(tag_id: uuid.UUID, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Update an existing tag.

    Supported fields in payload:
        - ``name``: new tag name (non-empty string)
        - ``type``: ``"income"``, ``"expense"`` or ``"both"``

    Args:
        tag_id: UUID of the tag to update.
        data: JSON payload.

    Returns:
        A tuple of (payload dict, status). On success the payload contains
        ``id`` and a success ``message``.
    """
    import uuid
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return {"error": "Tag not found"}, 404
    try:
        if "name" in data:
            new_name = (data.get("name") or "").strip()
            if not new_name:
                return {"error": "Tag name cannot be empty"}, 400
            # ensure no duplicate names for the same user
            other = (
                db.session.query(Tag)
                .filter(Tag.user_id == tag.user_id, Tag.name == new_name, Tag.id != tag.id)
                .first()
            )
            if other:
                return {"error": "Tag name already exists for this user"}, 400
            tag.name = new_name
        if "type" in data and data.get("type") is not None:
            raw_type = data.get("type")
            try:
                tag.type = TagType(raw_type)
            except ValueError:
                return {"error": "Invalid tag type"}, 400
        db.session.commit()
        return {"id": str(tag.id), "message": "Tag updated successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def delete_tag(tag_id: uuid.UUID) -> Tuple[Dict[str, Any], int]:
    """
    Delete a tag.

    Before deletion the tag is detached from any associated incomes and receipts.
    Counters and types are updated through ``register_tag_unassigned``.

    Args:
        tag_id: UUID of the tag to delete.

    Returns:
        A tuple of (payload dict, status). On success the payload contains
        a success ``message``.
    """
    import uuid
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return {"error": "Tag not found"}, 404
    try:
        # detach tag from incomes
        for inc in list(tag.incomes):
            inc.tag = None
            register_tag_unassigned(tag)
        # detach tag from receipts
        for rec in list(tag.receipts):
            rec.tag = None
            register_tag_unassigned(tag)
        db.session.delete(tag)
        db.session.commit()
        return {"message": "Tag deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


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
