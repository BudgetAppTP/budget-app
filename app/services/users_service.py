from app.extensions import db
from app.models import User
import uuid
from werkzeug.security import generate_password_hash

def get_all_users():
    """Возвращает всех пользователей."""
    users = db.session.query(User).all()
    return [
        {
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


def create_user(data):
    """
    Create a new user record.

    Expected keys in ``data`` are ``username``, ``email``, and
    ``password`` (plain text). The password is hashed server-side
    using werkzeug's PBKDF2 implementation. If a ``password_hash`` key
    is supplied instead, it is used verbatim. Additional fields are
    ignored.
    """
    try:
        username = data.get("username")
        email = data.get("email")
        # Accept either password or password_hash. Prefer hashing if a
        # plain password is provided.
        password = data.get("password")
        password_hash = data.get("password_hash")

        if not username or not email or not (password or password_hash):
            return {"error": "Missing required fields"}, 400
        if password and not password_hash:
            password_hash = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_verified=True,
        )
        db.session.add(new_user)
        db.session.commit()
        return {"id": str(new_user.id), "message": "User created successfully"}, 201
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
