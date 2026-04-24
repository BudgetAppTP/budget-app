from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from app import create_app
from app.extensions import db
from app.models import Account, AccountMember, AccountType, Receipt, ReceiptItem
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()


def register_and_login(client, email, password="pass"):
    reg = client.post("/api/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200


def _create_receipt(user_id, account_id, amount):
    receipt = Receipt(
        user_id=UUID(str(user_id)),
        account_id=UUID(str(account_id)),
        description="Analytics fixture",
        issue_date=date(2025, 10, 10),
        total_amount=Decimal(str(amount)),
    )
    db.session.add(receipt)
    db.session.flush()
    db.session.add(
        ReceiptItem(
            receipt_id=receipt.id,
            user_id=UUID(str(user_id)),
            name="Fixture item",
            quantity=Decimal("1"),
            unit_price=Decimal(str(amount)),
            total_price=Decimal(str(amount)),
        )
    )


def _create_secondary_account(user_id):
    account = Account(
        name="Secondary account",
        balance=Decimal("0"),
        currency="EUR",
        account_type=AccountType.ACCOUNT,
    )
    db.session.add(account)
    db.session.flush()
    db.session.add(
        AccountMember(
            user_id=UUID(str(user_id)),
            account_id=account.id,
            role="owner",
        )
    )
    return account.id


def test_donut_analytics_uses_authenticated_users_main_account(app):
    first = app.test_client()
    second = app.test_client()

    register_and_login(first, "analytics-first@test.local")
    register_and_login(second, "analytics-second@test.local")

    first_user_id = first.get("/api/auth/me").get_json()["data"]["id"]
    second_user_id = second.get("/api/auth/me").get_json()["data"]["id"]
    first_account_id = first.get("/api/account").get_json()["data"]["id"]
    second_account_id = second.get("/api/account").get_json()["data"]["id"]

    with app.app_context():
        _create_receipt(first_user_id, first_account_id, "10.00")
        first_secondary_account_id = _create_secondary_account(first_user_id)
        _create_receipt(first_user_id, first_secondary_account_id, "90.00")
        _create_receipt(second_user_id, second_account_id, "30.00")
        db.session.commit()

    own = first.get("/api/analytics/donut?year=2025&month=10")
    assert own.status_code == 200
    assert own.get_json()["data"]["total_amount"] == 10.0

    ignored = first.get(
        f"/api/analytics/donut?year=2025&month=10&account_id={second_account_id}"
    )
    assert ignored.status_code == 200
    assert ignored.get_json()["data"]["total_amount"] == 10.0


def test_donut_analytics_rejects_year_outside_date_range(app):
    client = app.test_client()
    register_and_login(client, "analytics-year@test.local")

    response = client.get("/api/analytics/donut?year=0&month=1")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "bad_request"
    assert response.get_json()["error"]["message"] == "Year must be a valid calendar year"
