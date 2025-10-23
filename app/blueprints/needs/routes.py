from . import bp
from flask import Blueprint, render_template

@bp.get("/")
def index():
    return render_template("needs/index.html")
