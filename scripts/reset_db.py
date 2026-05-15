from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions import db
from app.models import User


def reset_all() -> None:
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset complete: all tables recreated, users=0.")


def delete_users() -> None:
    app = create_app()
    with app.app_context():
        users = db.session.execute(db.select(User)).scalars().all()
        for user in users:
            db.session.delete(user)
        db.session.commit()
        remaining = db.session.execute(db.select(db.func.count()).select_from(User)).scalar()
        print(f"Deleted users: {len(users)}. Remaining users: {remaining}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset the local development database.")
    parser.add_argument(
        "--users-only",
        action="store_true",
        help="Delete registered users and their related data, keep the table schema.",
    )
    args = parser.parse_args()

    if args.users_only:
        delete_users()
    else:
        reset_all()


if __name__ == "__main__":
    main()
