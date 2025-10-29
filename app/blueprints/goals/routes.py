import uuid
from flask import render_template, request, redirect, url_for, flash, current_app
from . import bp
from .forms import GoalsFilterForm, GoalForm
from app.core.domain import Goal, Section

def _services():
    return current_app.extensions["services"]

@bp.route("/", methods=["GET", "POST"])
def index():
    form = GoalsFilterForm(request.values)
    section = form.section.data or ""
    if section:
        rows = _services().goals.by_section(Section(section))
    else:
        rows = _services().goals.all()
    return render_template("goals/index.html", form=form, rows=rows)

@bp.route("/edit", methods=["GET", "POST"])
@bp.route("/edit/<id>", methods=["GET", "POST"])
def edit(id=None):
    svc = _services()
    data = None
    if id:
        for g in svc.goals.all():
            if g.id == id:
                data = g
                break
    form = GoalForm(obj=data)
    if form.validate_on_submit():
        gid = id or str(uuid.uuid4())
        section_val = form.section.data or None
        section = Section(section_val) if section_val else None
        g = Goal(
            id=gid,
            name=form.name.data,
            type=form.type.data,
            target_amount=form.target_amount.data,
            section=section,
            month_from=form.month_from.data or None,
            month_to=form.month_to.data or None,
            is_done=bool(form.is_done.data),
        )
        svc.goals.upsert(g)
        flash("Ciel bol ulozeny.", "success")
        return redirect(url_for("goals.index"))
    return render_template("goals/edit.html", form=form, id=id)
