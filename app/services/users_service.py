import re

from app.extensions import db
from app.models import User
import uuid

from app.validators.user_validators import validate_user_create_data

EMAIL_REGEX = r"^[^@]+@[^@]+\.[^@]+$"

def get_all_users():
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
        validated, err, status = validate_user_create_data(data)
        if err:
            return err, status

        existing_user = db.session.query(User).filter_by(username=validated["username"]).first()
        if existing_user:
            return {"error": "Username already exists"}, 400

        existing_email = db.session.query(User).filter_by(email=validated["email"]).first()
        if existing_email:
            return {"error": "Email already exists"}, 400

        new_user = User(
            username=validated["username"],
            email=validated["email"],
            password_hash=validated["password_hash"]
        )

        db.session.add(new_user)
        db.session.commit()

        return {"id": str(new_user.id), "message": "User created successfully"}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
