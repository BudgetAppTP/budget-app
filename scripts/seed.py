"""Database seeder script for local development.

This script populates the database with sample data for testing and development.
It drops all tables, recreates them, and inserts seed data.

Usage:
    python -m scripts.seed

Note: This script will refuse to run in production environments.
"""

import hashlib
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

from tabulate import tabulate

from app import create_app
from app.extensions import db
from app.models import (
    Account,
    AccountMember,
    Category,
    FinancialTarget,
    Income,
    Receipt,
    ReceiptItem,
    Tag,
    User,
)
from app.models.base import Base
from app.utils.types import TagType


def check_environment():
    """Prevent running seeder in production environment."""
    env = os.getenv("APP_ENV", "development").lower()
    if env == "production":
        print("ERROR: Cannot run seeder in production environment!")
        print("Set APP_ENV to 'development' or 'test' to proceed.")
        sys.exit(1)
    print(f"Environment check passed: {env}")


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_users():
    users_data = [
        {
            "username": "johndoe",
            "email": "john.doe@example.com",
            "password": "password123",
        },
        {
            "username": "janedoe",
            "email": "jane.doe@example.com",
            "password": "password123",
        },
        {
            "username": "testuser",
            "email": "test@example.com",
            "password": "test123",
        },
    ]

    users = [
        User(
            username=data["username"],
            email=data["email"],
            password_hash=hash_password(data["password"]),
        )
        for data in users_data
    ]

    db.session.add_all(users)
    db.session.flush()
    return users


def seed_tags(users):
    expense_tags = ["Quantum Mart", "Byte & Bean Café", "The Electric Bazaar"]
    income_tags = ["Nebula Freelance Network", "NovaTech Solutions"]

    tags = []

    for user in users:
        for tag_name in expense_tags:
            tag = Tag(
                user_id=user.id,
                name=tag_name,
                type=None,
                counter=0
            )
            tags.append(tag)

        for tag_name in income_tags:
            tag = Tag(
                user_id=user.id,
                name=tag_name,
                type=None,
                counter=0
            )
            tags.append(tag)

    db.session.add_all(tags)
    db.session.flush()
    return tags


def seed_accounts(users):
    accounts_data = [
        {"key": "john_main", "name": "John Main Budget", "balance": Decimal("1250.00"), "currency": "EUR"},
        {"key": "jane_main", "name": "Jane Personal Budget", "balance": Decimal("820.50"), "currency": "EUR"},
        {"key": "family_shared", "name": "Family Shared Budget", "balance": Decimal("3400.00"), "currency": "EUR"},
        {"key": "test_solo", "name": "Test User Budget", "balance": Decimal("150.25"), "currency": "USD"},
    ]

    accounts = [
        Account(
            name=data["name"],
            balance=data["balance"],
            currency=data["currency"],
        )
        for data in accounts_data
    ]
    db.session.add_all(accounts)
    db.session.flush()

    account_map = {
        data["key"]: account
        for data, account in zip(accounts_data, accounts)
    }

    memberships_data = [
        {"user_idx": 0, "account_key": "john_main", "role": "owner"},
        {"user_idx": 1, "account_key": "jane_main", "role": "owner"},
        {"user_idx": 2, "account_key": "test_solo", "role": "owner"},
        {"user_idx": 0, "account_key": "family_shared", "role": "owner"},
        {"user_idx": 1, "account_key": "family_shared", "role": "owner"},
    ]

    memberships = [
        AccountMember(
            user_id=users[data["user_idx"]].id,
            account_id=account_map[data["account_key"]].id,
            role=data["role"],
        )
        for data in memberships_data
    ]
    db.session.add_all(memberships)
    db.session.flush()

    return accounts, memberships, account_map


def seed_categories(users):
    # NOTE: Global categories (no user_id) are included for now.
    # Future versions may drop support for general categories
    # depending on front-end implementation choices or data model updates.
    global_categories_data = [
        {"name": "Groceries", "parent": None},
        {"name": "Transport", "parent": None},
        {"name": "Entertainment", "parent": None},
    ]

    # User-specific categories
    user_categories_data = [
        {"name": "Household", "parent": None, "user_idx": 0},
        {"name": "Health", "parent": None, "user_idx": 0},
        {"name": "Education", "parent": None, "user_idx": 1},
    ]

    # Child categories
    child_categories_data = [
        {"name": "Fruits and Vegetables", "parent_name": "Groceries", "user_idx": None},
        {"name": "Meat and Fish", "parent_name": "Groceries", "user_idx": None},
    ]

    global_categories = [
        Category(name=data["name"], user_id=None, parent_id=None)
        for data in global_categories_data
    ]

    user_categories = [
        Category(name=data["name"], user_id=users[data["user_idx"]].id, parent_id=None)
        for data in user_categories_data
    ]

    db.session.add_all(global_categories + user_categories)
    db.session.flush()

    parent_map = {
        data["name"]: category
        for data, category in zip(
            global_categories_data + user_categories_data,
            global_categories + user_categories
        )
    }

    child_categories = [
        Category(
            name=data["name"],
            user_id=(users[data["user_idx"]].id if data["user_idx"] is not None else None),
            parent_id=(parent_map.get(data["parent_name"]).id if parent_map.get(data["parent_name"]) else None),
        )
        for data in child_categories_data
    ]

    db.session.add_all(child_categories)
    db.session.flush()

    return [*global_categories, *user_categories, *child_categories]


def seed_incomes(users, tags):
    today = date.today()

    def get_user_tag(user_idx, tag_name):
        return next(
            (tag for tag in tags if tag.user_id == users[user_idx].id and tag.name == tag_name),
            None
        )

    incomes_data = [
        {
            "user_idx": 0,
            "tag_name": "Nebula Freelance Network",
            "amount": Decimal("3200.00"),
            "income_date": today.replace(day=1) - timedelta(days=5),
        },
        {
            "user_idx": 0,
            "tag_name": "Nebula Freelance Network",
            "amount": Decimal("3200.00"),
            "income_date": today.replace(day=1),
        },
        {
            "user_idx": 1,
            "tag_name": "NovaTech Solutions",
            "amount": Decimal("1850.75"),
            "income_date": today - timedelta(days=10),
        },
        {
            "user_idx": 2,
            "tag_name": None,
            "amount": Decimal("950.00"),
            "income_date": today - timedelta(days=2),
        },
    ]

    incomes = []
    tags_used = []

    for data in incomes_data:
        tag = get_user_tag(data["user_idx"], data["tag_name"]) if data["tag_name"] else None

        income = Income(
            user_id=users[data["user_idx"]].id,
            tag_id=tag.id if tag else None,
            amount=data["amount"],
            income_date=data["income_date"],
            description=f"{data['tag_name'] or 'Unknown Source'}"
        )
        incomes.append(income)

        if tag:
            tags_used.append(tag)

    db.session.add_all(incomes)
    db.session.flush()

    for tag in tags_used:
        tag.increment_counter()

    unique_tags = set(tags_used)
    for tag in unique_tags:
        tag.update_type()

    return incomes


def seed_financial_targets(users):
    today = date.today()

    targets_data = [
        {
            "user_idx": 0,
            "title": "Vacation on Luna Shores",
            "target_amount": Decimal("1500.00"),
            "current_amount": Decimal("450.00"),
            "deadline_date": today + timedelta(days=180),
            "is_completed": False,
        },
        {
            "user_idx": 0,
            "title": "New HoloBook Pro",
            "target_amount": Decimal("1200.00"),
            "current_amount": Decimal("1200.00"),
            "deadline_date": today - timedelta(days=10),
            "is_completed": True,
        },
        {
            "user_idx": 1,
            "title": "Emergency Credit Reserve",
            "target_amount": Decimal("3000.00"),
            "current_amount": Decimal("1850.75"),
            "deadline_date": today + timedelta(days=365),
            "is_completed": False,
        },
    ]

    targets = [
        FinancialTarget(
            user_id=users[data["user_idx"]].id,
            title=data["title"],
            target_amount=data["target_amount"],
            current_amount=data["current_amount"],
            deadline_date=data["deadline_date"],
            is_completed=data["is_completed"],
        )
        for data in targets_data
    ]

    db.session.add_all(targets)
    db.session.flush()
    return targets


def seed_receipts(users, tags, account_map):
    today = date.today()

    def get_user_tag(user_idx, tag_name):
        return next(
            (tag for tag in tags if tag.user_id == users[user_idx].id and tag.name == tag_name),
            None
        )

    receipts_data = [
        {
            "user_idx": 0,
            "account_key": "family_shared",
            "tag_name": "Quantum Mart",
            "issue_date": today - timedelta(days=2),
            "total_amount": Decimal("45.80"),
            "external_uid": "QTM-2025-001234",
        },
        {
            "user_idx": 0,
            "account_key": "john_main",
            "tag_name": "Byte & Bean Café",
            "issue_date": today - timedelta(days=5),
            "total_amount": Decimal("28.50"),
        },
        {
            "user_idx": 1,
            "account_key": "family_shared",
            "tag_name": "The Electric Bazaar",
            "issue_date": today - timedelta(days=1),
            "total_amount": Decimal("67.20"),
            "external_uid": "EBZ-2025-005678",
        },
        {
            "user_idx": 0,
            "account_key": "john_main",
            "tag_name": "Quantum Mart",
            "issue_date": today - timedelta(days=10),
            "total_amount": Decimal("102.15"),
        },
        {
            "user_idx": 2,
            "account_key": "test_solo",
            "tag_name": "Byte & Bean Café",
            "issue_date": today,
            "total_amount": Decimal("34.90"),
        },
    ]

    receipts = []
    tags_used = []

    for data in receipts_data:
        tag = get_user_tag(data["user_idx"], data["tag_name"])

        receipt = Receipt(
            user_id=users[data["user_idx"]].id,
            account_id=account_map[data["account_key"]].id,
            tag_id=tag.id if tag else None,
            issue_date=data["issue_date"],
            total_amount=data["total_amount"],
            external_uid=data.get("external_uid"),
            description=f"{data['tag_name'] or 'Unknown Vendor'}"
        )
        receipts.append(receipt)

        if tag:
            tags_used.append(tag)

    db.session.add_all(receipts)
    db.session.flush()

    for tag in tags_used:
        tag.increment_counter()

    unique_tags = set(tags_used)
    for tag in unique_tags:
        tag.update_type()

    return receipts


def seed_receipt_items(receipts, categories, users):
    food_cat = next((c for c in categories if c.name == "Groceries"), None)
    fruit_cat = next((c for c in categories if c.name == "Fruits and Vegetables"), None)
    meat_cat = next((c for c in categories if c.name == "Meat and Fish"), None)

    # Items for receipt 0 (Quantum Mart)
    items_r0 = [
        {"name": "Organic Milk 1L", "quantity": Decimal("2"), "unit_price": Decimal("0.95"), "category": food_cat},
        {"name": "Sliced Bread", "quantity": Decimal("1"), "unit_price": Decimal("1.20"), "category": food_cat},
        {"name": "Apples", "quantity": Decimal("2.5"), "unit_price": Decimal("1.80"), "category": fruit_cat},
        {"name": "Chicken Breast", "quantity": Decimal("0.8"), "unit_price": Decimal("7.50"), "category": meat_cat},
        {"name": "Tomatoes", "quantity": Decimal("1.2"), "unit_price": Decimal("2.90"), "category": fruit_cat},
        {"name": "Garlic", "quantity": Decimal("1"), "unit_price": Decimal("0.85"), "category": food_cat},
        {"name": "Potatoes 2kg", "quantity": Decimal("1"), "unit_price": Decimal("2.50"), "category": fruit_cat},
        {"name": "Sunflower Oil", "quantity": Decimal("1"), "unit_price": Decimal("3.20"), "category": food_cat},
    ]

    # Items for receipt 1 (Byte & Bean Café)
    items_r1 = [
        {"name": "Greek Yogurt", "quantity": Decimal("4"), "unit_price": Decimal("0.65"), "category": food_cat},
        {"name": "Smoked Ham", "quantity": Decimal("0.3"), "unit_price": Decimal("12.00"), "category": meat_cat},
        {"name": "Cheddar Cheese", "quantity": Decimal("0.4"), "unit_price": Decimal("8.50"), "category": food_cat},
        {"name": "Bananas", "quantity": Decimal("1.5"), "unit_price": Decimal("1.80"), "category": fruit_cat},
    ]

    # Items for receipt 2 (The Electric Bazaar)
    items_r2 = [
        {"name": "Beef Steak", "quantity": Decimal("1.2"), "unit_price": Decimal("15.00"), "category": meat_cat},
        {"name": "Blue Cheese", "quantity": Decimal("0.25"), "unit_price": Decimal("12.00"), "category": food_cat},
        {"name": "Red Wine", "quantity": Decimal("1"), "unit_price": Decimal("6.50"), "category": None},
        {"name": "Olives", "quantity": Decimal("1"), "unit_price": Decimal("2.90"), "category": food_cat},
        {"name": "Pasta", "quantity": Decimal("2"), "unit_price": Decimal("1.45"), "category": food_cat},
    ]

    all_items_data = [
        (receipts[0], items_r0, users[0]),
        (receipts[1], items_r1, users[0]),
        (receipts[2], items_r2, users[1]),
    ]

    items = [
        ReceiptItem(
            receipt_id=receipt.id,
            user_id=user.id,
            category_id=(data.get("category").id if data.get("category") else None),
            name=data["name"],
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            total_price=data["quantity"] * data["unit_price"],
        )
        for receipt, items_data, user in all_items_data
        for data in items_data
    ]

    db.session.add_all(items)
    db.session.flush()
    return items


def main():
    print("=" * 60)
    print("DATABASE SEEDER - Development Environment")
    print("=" * 60)

    check_environment()

    print("\nInitializing Flask application...")
    app = create_app()

    with app.app_context():
        print("Dropping all tables...")
        Base.metadata.drop_all(db.engine)
        Base.metadata.create_all(db.engine)

        # Seeding order matters — later entities depend on earlier ones.
        users = seed_users()
        accounts, memberships, account_map = seed_accounts(users)
        tags = seed_tags(users)
        categories = seed_categories(users)
        incomes = seed_incomes(users, tags)
        targets = seed_financial_targets(users)
        receipts = seed_receipts(users, tags, account_map)
        items = seed_receipt_items(receipts, categories, users)

        db.session.commit()

        stats = [
            ("Users", len(users)),
            ("Accounts", len(accounts)),
            ("Account Members", len(memberships)),
            ("Tags", len(tags)),
            ("Categories", len(categories)),
            ("Incomes", len(incomes)),
            ("Financial Targets", len(targets)),
            ("Receipts", len(receipts)),
            ("Receipt Items", len(items)),
        ]

        print("\nSeed Summary:")
        print(tabulate(stats, headers=["Table", "Records"], tablefmt="grid"))
        print("\nSeeding completed successfully!")


if __name__ == "__main__":
    main()
