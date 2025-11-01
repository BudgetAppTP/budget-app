import uuid
from flask import current_app, request
from app.api import bp, make_response
from app.core.domain import Goal, Section

def _services():
    return current_app.extensions["services"]

@bp.get("/goals")
def api_goals_list():
    section = (request.args.get("section") or "").strip()
    if section:
        rows = _services().goals.by_section(Section(section))
    else:
        rows = _services().goals.all()
    items = []
    for g in rows:
        items.append({
            "id": g.id,
            "name": g.name,
            "type": g.type,
            "target_amount": float(g.target_amount),
            "section": str(g.section) if g.section else None,
            "month_from": g.month_from,
            "month_to": g.month_to,
            "is_done": bool(g.is_done),
        })
    return make_response({"items": items, "count": len(items)})

@bp.post("/goals")
def api_goals_create():
    p = request.get_json(silent=True) or {}
    gid = str(uuid.uuid4())
    section_val = p.get("section") or None
    section = Section(section_val) if section_val else None
    g = Goal(
        id=gid,
        name=p.get("name", ""),
        type=p.get("type", ""),
        target_amount=p.get("target_amount", 0),
        section=section,
        month_from=p.get("month_from") or None,
        month_to=p.get("month_to") or None,
        is_done=bool(p.get("is_done", False)),
    )
    _services().goals.upsert(g)
    return make_response({"id": gid}, None, 201)

@bp.put("/goals/<id>")
def api_goals_update(id):
    p = request.get_json(silent=True) or {}
    section_val = p.get("section") or None
    section = Section(section_val) if section_val else None
    g = Goal(
        id=id,
        name=p.get("name", ""),
        type=p.get("type", ""),
        target_amount=p.get("target_amount", 0),
        section=section,
        month_from=p.get("month_from") or None,
        month_to=p.get("month_to") or None,
        is_done=bool(p.get("is_done", False)),
    )
    _services().goals.upsert(g)
    return make_response({"ok": True})
