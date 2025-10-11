from flask import Blueprint, render_template
from app.models import User


bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/users')
def users():
    users = User.query.all()
    return str(users)
