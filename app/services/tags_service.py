from __future__ import annotations

import uuid
from typing import Any

from app.extensions import db
from app.models import Tag, User
from app.models.tag import TagType
from app.services.errors import BadRequestError, NotFoundError
from app.services.responses import CreatedResult, OkResult

from app.validators.tag_validators import validate_tag_create_data, validate_tag_update_data


def get_or_create_user_tag(user_id: uuid.UUID, name: str) -> Tag:
    tag = (
        db.session.query(Tag)
        .filter(Tag.user_id == user_id, Tag.name == name)
        .first()
    )
    if tag:
        return tag

    tag = Tag(
        user_id=user_id,
        name=name,
        # type is initially None; it will be inferred by update_type()
        type=None,
        counter=0,
    )
    db.session.add(tag)
    db.session.flush()
    return tag


def find_or_create_tag_from_ekasa(user_id: uuid.UUID, data: dict) -> Tag | None:
    name = data.get("name")
    if not name:
        return None
    return get_or_create_user_tag(user_id, name)


def register_tag_assigned(tag: Tag) -> None:
    """Update usage when a tag is assigned to an income or receipt."""
    if tag is None:
        return

    tag.increment_counter()
    tag.update_type()


def register_tag_unassigned(tag: Tag) -> None:
    """Update usage when a tag is removed from an income or receipt."""
    if tag is None:
        return

    tag.decrement_counter()
    tag.update_type()


def _serialize_tag(tag: Tag, *, enum_mode: str = "value") -> dict[str, Any]:
    return {
        "id": str(tag.id),
        "user_id": str(tag.user_id),
        "name": tag.name,
        "type": tag.type.value if tag.type is not None and enum_mode == "value"
        else tag.type.name if tag.type is not None
        else None,
        "counter": int(tag.counter) if tag.counter is not None else 0,
    }


def _get_tag_for_user(tag_id: uuid.UUID, user_id: uuid.UUID) -> Tag:
    tag = db.session.get(Tag, tag_id)
    if tag is None or tag.user_id != user_id:
        raise NotFoundError("Tag not found")
    return tag


def _find_duplicate_user_tag(
    user_id: uuid.UUID,
    name: str,
    exclude_tag_id: uuid.UUID | None = None,
) -> Tag | None:
    query = db.session.query(Tag).filter(
        Tag.user_id == user_id,
        Tag.name == name,
    )
    if exclude_tag_id is not None:
        query = query.filter(Tag.id != exclude_tag_id)
    return query.first()


def _tag_has_linked_records(tag: Tag) -> bool:
    return bool(tag.incomes) or bool(tag.receipts)


def get_tags_by_type(tag_type: TagType, user_id: uuid.UUID) -> OkResult:
    if tag_type not in (TagType.INCOME, TagType.EXPENSE):
        raise BadRequestError("Invalid tag type")

    query = db.session.query(Tag).filter(Tag.type.in_([tag_type, TagType.BOTH]))
    query = query.filter(Tag.user_id == user_id)
    tags = query.order_by(Tag.name.asc()).all()
    items = [_serialize_tag(tag) for tag in tags]
    return OkResult({"tags": items, "count": len(items)})


def create_tag(data: dict, user_id: uuid.UUID) -> CreatedResult:
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")

    validated = validate_tag_create_data(data)

    try:
        tag = get_or_create_user_tag(user_id, validated["name"])
        if validated["type"] is not None:
            tag.type = validated["type"]
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return CreatedResult({"id": str(tag.id), "message": "Tag created successfully"})


def update_tag(tag_id: uuid.UUID, data: dict, user_id: uuid.UUID) -> OkResult:
    tag = _get_tag_for_user(tag_id, user_id)
    validated = validate_tag_update_data(data)

    if "name" in validated:
        other = _find_duplicate_user_tag(
            tag.user_id,
            validated["name"],
            exclude_tag_id=tag.id,
        )
        if other:
            raise BadRequestError("Tag name already exists for this user")
        tag.name = validated["name"]

    if "type" in validated:
        if _tag_has_linked_records(tag):
            tag.update_type()
        else:
            tag.type = validated["type"]

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult({"id": str(tag.id), "message": "Tag updated successfully"})


def delete_tag(tag_id: uuid.UUID, user_id: uuid.UUID) -> OkResult:
    tag = _get_tag_for_user(tag_id, user_id)

    tagged_records = [*list(tag.incomes), *list(tag.receipts)]
    for tagged_record in tagged_records:
        tagged_record.tag = None
        register_tag_unassigned(tag)

    try:
        db.session.delete(tag)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return OkResult({"message": "Tag deleted successfully"})


def get_income_tags(user_id: uuid.UUID) -> OkResult:
    query = db.session.query(Tag).filter(
        Tag.type.in_([TagType.INCOME, TagType.BOTH])
    )

    query = query.filter(Tag.user_id == user_id)

    tags = query.order_by(Tag.name.asc()).all()
    return OkResult({"success": True, "tags": [_serialize_tag(tag, enum_mode="name") for tag in tags]})


def get_expense_tags(user_id: uuid.UUID) -> OkResult:
    query = db.session.query(Tag).filter(
        Tag.type.in_([TagType.EXPENSE, TagType.BOTH])
    )

    query = query.filter(Tag.user_id == user_id)

    tags = query.order_by(Tag.name.asc()).all()
    return OkResult({"success": True, "tags": [_serialize_tag(tag, enum_mode="name") for tag in tags]})
