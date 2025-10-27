from app.extensions import db
from app.models import User
import uuid

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
    try:
        username = data.get("username")
        email = data.get("email")
        password_hash = data.get("password_hash")

        if not all([username, email, password_hash]):
            return {"error": "Missing required fields"}, 400

        new_user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password_hash=password_hash
        )

        db.session.add(new_user)
        db.session.commit()

        return {"id": str(new_user.id), "message": "User created successfully"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
