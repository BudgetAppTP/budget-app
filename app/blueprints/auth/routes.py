from flask import render_template, request, redirect, url_for, flash, current_app
from . import bp
from .forms import LoginForm, RegisterForm
from app.core.domain import User
import uuid

def _services():
    return current_app.extensions["services"]

@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        svc = _services()
        ok = svc.auth.login(form.email.data, form.password.data, svc.users)
        if ok:
            flash("Prihlasenie prebehlo uspesne.", "success")
            return redirect(url_for("dashboard.index"))
        flash("Neplatne prihlasenie.", "danger")
    return render_template("auth/login.html", form=form)

@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        svc = _services()
        if svc.users.get_by_email(form.email.data):
            flash("Pouzivatel s tymto emailom uz existuje.", "warning")
            return render_template("auth/register.html", form=form)
        uid = str(uuid.uuid4())
        pwd_hash = svc.auth.hash_password(form.password.data)
        svc.users.add(User(uid, form.email.data, pwd_hash))
        flash("Ucet bol vytvoreny. Mozete sa prihlasit.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)

@bp.route("/logout")
def logout():
    _services().auth.logout()
    flash("Odhlaseny.", "info")
    return redirect(url_for("auth.login"))
