import hashlib
from flask import session
from typing import Optional
from app.core.domain import User
from .repositories import UsersRepository

class AuthServiceStub:
    def hash_password(self, raw: str) -> str:
        return hashlib.sha256(("salt::" + raw).encode("utf-8")).hexdigest()

    def verify(self, raw: str, hashed: str) -> bool:
        return self.hash_password(raw) == hashed

    def login(self, email: str, password: str, users: UsersRepository) -> bool:
        u = users.get_by_email(email)
        if not u:
            return False
        if not self.verify(password, u.password_hash):
            return False
        session["uid"] = u.id
        session["email"] = u.email
        return True

    def logout(self):
        session.pop("uid", None)
        session.pop("email", None)

    def current_user(self, users: UsersRepository) -> Optional[User]:
        uid = session.get("uid")
        if not uid:
            return None
        for u in users._items:
            if u.id == uid:
                return u
        return None
