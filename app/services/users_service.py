import uuid

from sqlalchemy.exc import IntegrityError

from app.core.validators import is_valid_iso4217
from app.extensions import db
from app.models import Account, AccountMember, AccountType, User
from app.services.errors import BadRequestError, ConflictError
from app.services.responses import CreatedResult, OkResult
from app.validators.user_validators import validate_user_create_data


def _create_main_account_for_user(user_id: uuid.UUID, currency: str = "EUR") -> Account:
    account = Account(
        name="Main Account",
        balance=0,
        currency=currency,
        account_type=AccountType.ACCOUNT,
    )
    db.session.add(account)
    db.session.flush()

    membership = AccountMember(
        user_id=user_id,
        account_id=account.id,
        role="owner",
    )
    db.session.add(membership)
    return account


def create_user_with_main_account(
    *,
    username: str,
    email: str,
    password_hash: str,
    currency: str = "EUR",
    is_verified: bool = False,
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        is_verified=is_verified,
    )
    db.session.add(user)
    db.session.flush()
    _create_main_account_for_user(user.id, currency)
    return user


def _ensure_unique_username(base_username: str) -> str:
    username = base_username[:32] or "user"
    exists = db.session.query(User).filter(User.username == username).first()
    if not exists:
        return username

    suffix = 1
    while True:
        candidate = f"{base_username[:24]}{suffix:08d}"[:32]
        exists = db.session.query(User).filter(User.username == candidate).first()
        if not exists:
            return candidate
        suffix += 1


def ensure_user_for_auth_register(email: str, password_hash: str, default_currency: str = "EUR") -> User:
    """Ensure DB user exists for auth/register flow and has a main account."""
    user = db.session.query(User).filter(User.email == email).first()
    if user is not None:
        return user

    local_part = email.split("@", 1)[0].strip().lower().replace(" ", "")
    username = _ensure_unique_username(local_part or f"user_{uuid.uuid4().hex[:8]}")
    user = create_user_with_main_account(
        username=username,
        email=email,
        password_hash=password_hash,
        currency=default_currency,
    )
    db.session.commit()
    return user


def get_all_users():
    """Get all users in the system."""
    users = db.session.query(User).all()
    return OkResult([
        {
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ])


def create_user(data):
    validated = validate_user_create_data(data)

    existing_user = db.session.query(User).filter_by(username=validated["username"]).first()
    if existing_user:
        raise ConflictError("Username already exists")

    existing_email = db.session.query(User).filter_by(email=validated["email"]).first()
    if existing_email:
        raise ConflictError("User with this email already exists")

    try:
        new_user = create_user_with_main_account(
            username=validated["username"],
            email=validated["email"],
            password_hash=validated["password_hash"],
            currency=validated.get("currency", "EUR"),
        )
        db.session.commit()

        return CreatedResult({"id": str(new_user.id), "message": "User created successfully"})
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("User with this email already exists")
    except Exception:
        db.session.rollback()
        raise
