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
    Category,
    FinancialTarget,
    Income,
    Organization,
    Receipt,
    ReceiptItem,
    User,
)
from app.models.base import Base
from app.models.organization import OrganizationType


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


def seed_organizations():
    orgs_data = [
        {
            "name": "Quantum Mart",
            "type": OrganizationType.MERCHANT,
            "address": "42 Entanglement Avenue, Neo City",
            "website": "https://quantummart.fake",
        },
        {
            "name": "Byte & Bean Café",
            "type": OrganizationType.MERCHANT,
            "address": "7 Cloud Loop, Neo City",
            "website": "https://byteandbean.fake",
        },
        {
            "name": "The Electric Bazaar",
            "type": OrganizationType.MERCHANT,
            "address": "99 Circuit Street, Neo City",
            "website": "https://electricbazaar.fake",
        },
        {
            "name": "Nebula Freelance Network",
            "type": OrganizationType.INCOME_SOURCE,
            "address": "Orbital Hub 3, Neo City",
            "website": "https://nebulafreelance.fake",
            "contact_info": "contact@nebulafreelance.fake",
        },
        {
            "name": "NovaTech Solutions",
            "type": OrganizationType.BOTH,
            "address": "16 Quantum Plaza, Neo City",
            "website": "https://novatech.fake",
            "contact_info": "hr@novatech.fake",
        },
    ]

    organizations = [
        Organization(
            name=data["name"],
            type=data["type"],
            address=data.get("address"),
            website=data.get("website"),
            contact_info=data.get("contact_info"),
        )
        for data in orgs_data
    ]

    db.session.add_all(organizations)
    db.session.flush()
    return organizations


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


def seed_incomes(users, organizations):
    nebula = next(org for org in organizations if "Nebula" in org.name)
    novatech = next(org for org in organizations if "NovaTech" in org.name)

    today = date.today()

    incomes_data = [
        {
            "user_idx": 0,
            "organization": nebula,
            "amount": Decimal("3200.00"),
            "income_date": today.replace(day=1) - timedelta(days=5),  # Last month
        },
        {
            "user_idx": 0,
            "organization": nebula,
            "amount": Decimal("3200.00"),
            "income_date": today.replace(day=1),  # This month
        },
        {
            "user_idx": 1,
            "organization": novatech,
            "amount": Decimal("1850.75"),
            "income_date": today - timedelta(days=10),
        },
        {
            "user_idx": 2,
            "organization": None,
            "amount": Decimal("950.00"),
            "income_date": today - timedelta(days=2),
        },
    ]

    incomes = [
        Income(
            user_id=users[data["user_idx"]].id,
            organization_id=data["organization"].id if data["organization"] else None,
            amount=data["amount"],
            income_date=data["income_date"],
        )
        for data in incomes_data
    ]

    db.session.add_all(incomes)
    db.session.flush()
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


def seed_receipts(users, organizations):
    quantum_mart = next(org for org in organizations if "Quantum" in org.name)
    byte_bean = next(org for org in organizations if "Byte" in org.name)
    electric_bazaar = next(org for org in organizations if "Electric" in org.name)

    today = date.today()

    receipts_data = [
        {
            "user_idx": 0,
            "organization": quantum_mart,
            "issue_date": today - timedelta(days=2),
            "total_amount": Decimal("45.80"),
            "external_uid": "QTM-2025-001234",
        },
        {
            "user_idx": 0,
            "organization": byte_bean,
            "issue_date": today - timedelta(days=5),
            "total_amount": Decimal("28.50"),
        },
        {
            "user_idx": 1,
            "organization": electric_bazaar,
            "issue_date": today - timedelta(days=1),
            "total_amount": Decimal("67.20"),
            "external_uid": "EBZ-2025-005678",
        },
        {
            "user_idx": 0,
            "organization": quantum_mart,
            "issue_date": today - timedelta(days=10),
            "total_amount": Decimal("102.15"),
        },
        {
            "user_idx": 2,
            "organization": byte_bean,
            "issue_date": today,
            "total_amount": Decimal("34.90"),
        },
    ]

    receipts = [
        Receipt(
            user_id=users[data["user_idx"]].id,
            organization_id=data["organization"].id,
            issue_date=data["issue_date"],
            total_amount=data["total_amount"],
            external_uid=data.get("external_uid"),
        )
        for data in receipts_data
    ]

    db.session.add_all(receipts)
    db.session.flush()
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
        organizations = seed_organizations()
        categories = seed_categories(users)
        incomes = seed_incomes(users, organizations)
        targets = seed_financial_targets(users)
        receipts = seed_receipts(users, organizations)
        items = seed_receipt_items(receipts, categories, users)

        db.session.commit()

        stats = [
            ("Users", len(users)),
            ("Organizations", len(organizations)),
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
