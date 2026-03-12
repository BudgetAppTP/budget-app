import warnings

from app.extensions import db
from app.models import User
from app.services.errors import BadRequestError


def get_mock_user_id():
    warnings.warn(
        "Auth user resolution is not implemented yet. Using first available user.",
        RuntimeWarning,
        stacklevel=2,
    )

    fallback_user = db.session.query(User).order_by(User.created_at.asc()).first()
    if fallback_user is None:
        raise BadRequestError("Missing user context and no users exist")
    return fallback_user.id
