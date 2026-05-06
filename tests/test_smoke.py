"""
Smoke tests for the Budget Tracker application.

These tests verify that the application can start and basic infrastructure works.
"""
import io
import time
import uuid
from datetime import date
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Account, AccountMember, Category, Goal, Income, Receipt, ReceiptItem, SavingsFund, Tag, User
from app.services import ekasa_service
from app.services.errors import BadRequestError, UpstreamServiceError
from app.services.users_service import create_user_with_main_account
from scripts.seed import main as seed_main
from config import TestConfig


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app(TestConfig)

    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    email = "u@test.local"
    password = "pass"
    reg = client.post("/api/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return client


def assert_json_ok(resp):
    assert resp.status_code == 200
    assert resp.is_json
    body = resp.get_json()
    assert "data" in body
    assert "error" in body and body["error"] is None
    return body["data"]


def _get_user(email: str) -> User:
    return db.session.query(User).filter(User.email == email).one()


def _get_main_account(user: User) -> Account:
    return next(account for account in user.accounts if account.account_type.value == "account")


def test_health_ok(client):
    r = client.get("/api/health")
    data = assert_json_ok(r)
    assert data.get("status") == "ok"


def test_transactions_list_ok(auth_client):
    r = auth_client.get("/api/transactions")
    data = assert_json_ok(r)
    assert "items" in data
    assert "count" in data
    assert isinstance(data["items"], list)


def test_goals_list_ok(client):
    user_email = f"user_{uuid.uuid4().hex[:8]}@test.local"
    create = client.post(
        "/api/users",
        json={"username": f"user_{uuid.uuid4().hex[:8]}", "email": user_email, "password_hash": "hash"},
    )
    assert create.status_code == 201

    account_resp = client.get("/api/account")
    account_data = assert_json_ok(account_resp)
    assert account_data["account_type"] == "account"

    fund_resp = client.post(
        "/api/savings-funds",
        json={"name": "Vacation Fund", "currency": "EUR", "target_amount": "1000.00", "monthly_contribution": "100.00"},
    )
    assert fund_resp.status_code == 201
    fund_id = fund_resp.get_json()["data"]["id"]

    adjust_resp = client.post(
        f"/api/savings-funds/{fund_id}/balance-adjustments",
        json={"delta_amount": "500.00"},
    )
    assert_json_ok(adjust_resp)

    goal_resp = client.post(
        "/api/goals",
        json={"savings_fund_id": fund_id, "target_amount": "300.00"},
    )
    assert goal_resp.status_code == 201
    goal_id = goal_resp.get_json()["data"]["id"]
    assert goal_resp.get_json()["data"]["current_amount"] == 0.0

    allocate_resp = client.post(
        f"/api/goals/{goal_id}/allocate",
        json={"delta_amount": "300.00"},
    )
    assert_json_ok(allocate_resp)

    second_goal_resp = client.post(
        "/api/goals",
        json={"savings_fund_id": fund_id, "target_amount": "300.00"},
    )
    assert second_goal_resp.status_code == 201
    second_goal_id = second_goal_resp.get_json()["data"]["id"]

    over_allocate_resp = client.post(
        f"/api/goals/{second_goal_id}/allocate",
        json={"delta_amount": "250.00"},
    )
    assert over_allocate_resp.status_code == 400
    over_allocate_body = over_allocate_resp.get_json()
    assert over_allocate_body["error"]["message"] == "Insufficient unallocated savings fund balance"

    complete_resp = client.post(
        f"/api/goals/{goal_id}/complete",
    )
    complete_data = assert_json_ok(complete_resp)
    assert complete_data["is_completed"] is True

    reopen_resp = client.post(
        f"/api/goals/{goal_id}/reopen",
    )
    reopen_data = assert_json_ok(reopen_resp)
    assert reopen_data["is_completed"] is False

    list_resp = client.get("/api/goals")
    data = assert_json_ok(list_resp)
    assert "items" in data
    assert "count" in data
    assert data["count"] >= 1


def test_dashboard_ok(auth_client):
    r = auth_client.get("/api/dashboard/summary?year=2025&month=10")
    data = assert_json_ok(r)
    assert data.get("year") == 2025
    assert data.get("month") == 10
    for k in ["total_incomes", "total_expenses"]:
        assert k in data


def test_goals_without_mock_header_use_fallback_user(client):
    user_email = f"user_{uuid.uuid4().hex[:8]}@test.local"
    create = client.post(
        "/api/users",
        json={"username": f"user_{uuid.uuid4().hex[:8]}", "email": user_email, "password_hash": "hash"},
    )
    assert create.status_code == 201

    r = client.get("/api/goals")
    data = assert_json_ok(r)
    assert "warning" not in data


def test_goals_list_is_scoped_to_authenticated_user(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        older_user = create_user_with_main_account(
            username=f"older_{uuid.uuid4().hex[:8]}",
            email=f"older_{uuid.uuid4().hex[:8]}@test.local",
            password_hash="hash",
            is_verified=True,
        )
        db.session.flush()

        auth_fund = SavingsFund(
            name="Auth Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        older_fund = SavingsFund(
            name="Older Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("900.00"),
            monthly_contribution=Decimal("90.00"),
        )
        db.session.add_all([auth_fund, older_fund])
        db.session.flush()

        db.session.add_all([
            AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"),
            AccountMember(user_id=older_user.id, account_id=older_fund.id, role="owner"),
        ])
        db.session.flush()

        auth_goal = Goal(
            user_id=auth_user.id,
            savings_fund_id=auth_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("20.00"),
            is_completed=False,
        )
        older_goal = Goal(
            user_id=older_user.id,
            savings_fund_id=older_fund.id,
            target_amount=Decimal("999.00"),
            current_amount=Decimal("111.00"),
            is_completed=False,
        )
        db.session.add_all([auth_goal, older_goal])
        db.session.commit()

        auth_user_id = str(auth_user.id)
        auth_goal_id = str(auth_goal.id)

    r = auth_client.get("/api/goals")
    data = assert_json_ok(r)

    assert data["count"] == 1
    assert [item["id"] for item in data["items"]] == [auth_goal_id]
    assert data["items"][0]["user_id"] == auth_user_id


def test_goals_create_is_scoped_to_authenticated_user(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        older_user = create_user_with_main_account(
            username=f"older_{uuid.uuid4().hex[:8]}",
            email=f"older_{uuid.uuid4().hex[:8]}@test.local",
            password_hash="hash",
            is_verified=True,
        )
        db.session.flush()

        auth_fund = SavingsFund(
            name="Auth Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        older_fund = SavingsFund(
            name="Older Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("900.00"),
            monthly_contribution=Decimal("90.00"),
        )
        db.session.add_all([auth_fund, older_fund])
        db.session.flush()

        db.session.add_all([
            AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"),
            AccountMember(user_id=older_user.id, account_id=older_fund.id, role="owner"),
        ])
        db.session.commit()

        auth_fund_id = str(auth_fund.id)
        older_fund_id = str(older_fund.id)
        auth_user_id = str(auth_user.id)

    allowed_resp = auth_client.post(
        "/api/goals",
        json={"savings_fund_id": auth_fund_id, "target_amount": "120.00"},
    )
    assert allowed_resp.status_code == 201
    allowed_body = allowed_resp.get_json()
    assert allowed_body["data"]["user_id"] == auth_user_id
    assert allowed_body["data"]["savings_fund_id"] == auth_fund_id

    denied_resp = auth_client.post(
        "/api/goals",
        json={"savings_fund_id": older_fund_id, "target_amount": "120.00"},
    )
    assert denied_resp.status_code == 404
    denied_body = denied_resp.get_json()
    assert denied_body["error"]["message"] == "Savings fund not found"


def test_savings_funds_list_is_scoped_to_authenticated_user(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        older_user = create_user_with_main_account(
            username=f"older_fund_{uuid.uuid4().hex[:8]}",
            email=f"older_fund_{uuid.uuid4().hex[:8]}@test.local",
            password_hash="hash",
            is_verified=True,
        )
        db.session.flush()

        auth_fund = SavingsFund(
            name="Auth Fund",
            balance=Decimal("150.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        older_fund = SavingsFund(
            name="Older Fund",
            balance=Decimal("275.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("900.00"),
            monthly_contribution=Decimal("90.00"),
        )
        db.session.add_all([auth_fund, older_fund])
        db.session.flush()

        db.session.add_all([
            AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"),
            AccountMember(user_id=older_user.id, account_id=older_fund.id, role="owner"),
        ])
        db.session.commit()

        auth_fund_id = str(auth_fund.id)
        older_fund_id = str(older_fund.id)

    resp = auth_client.get("/api/savings-funds")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"]["count"] == 1
    assert [item["id"] for item in body["data"]["items"]] == [auth_fund_id]
    assert auth_fund_id != older_fund_id


def test_savings_funds_create_rejects_negative_planning_amounts(auth_client, app):
    resp = auth_client.post(
        "/api/savings-funds",
        json={
            "name": "Invalid Fund",
            "currency": "EUR",
            "target_amount": "-1.00",
            "monthly_contribution": "-5.00",
        },
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "target_amount must be greater than or equal to 0"

    with app.app_context():
        auth_user = _get_user("u@test.local")
        count = (
            db.session.query(SavingsFund)
            .join(AccountMember, AccountMember.account_id == SavingsFund.id)
            .filter(AccountMember.user_id == auth_user.id)
            .count()
        )
        assert count == 0


def test_savings_funds_update_rejects_negative_planning_amounts(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        auth_fund = SavingsFund(
            name="Update Fund",
            balance=Decimal("150.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        db.session.add(auth_fund)
        db.session.flush()

        db.session.add(AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"))
        db.session.commit()

        auth_fund_id = str(auth_fund.id)

    resp = auth_client.patch(
        f"/api/savings-funds/{auth_fund_id}",
        json={
            "target_amount": "-1.00",
            "monthly_contribution": "-5.00",
        },
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "target_amount must be greater than or equal to 0"

    with app.app_context():
        fund = db.session.get(SavingsFund, uuid.UUID(auth_fund_id))
        assert fund is not None
        assert fund.target_amount == Decimal("500.00")
        assert fund.monthly_contribution == Decimal("50.00")


def test_goals_update_allows_authenticated_owner_to_update_own_goal(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        auth_fund = SavingsFund(
            name="Update Auth Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        db.session.add(auth_fund)
        db.session.flush()

        db.session.add(AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"))
        db.session.flush()

        auth_goal = Goal(
            user_id=auth_user.id,
            savings_fund_id=auth_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("20.00"),
            is_completed=False,
        )
        db.session.add(auth_goal)
        db.session.commit()

        auth_goal_id = str(auth_goal.id)

    resp = auth_client.patch(
        f"/api/goals/{auth_goal_id}",
        json={"target_amount": "150.00"},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"]["id"] == auth_goal_id
    assert body["data"]["target_amount"] == 150.0

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(auth_goal_id))
        assert goal is not None
        assert goal.target_amount == Decimal("150.00")


def test_goals_update_rejects_foreign_goal_for_authenticated_user(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        older_user = create_user_with_main_account(
            username=f"older_{uuid.uuid4().hex[:8]}",
            email=f"older_{uuid.uuid4().hex[:8]}@test.local",
            password_hash="hash",
            is_verified=True,
        )
        db.session.flush()

        auth_fund = SavingsFund(
            name="Update Auth Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        older_fund = SavingsFund(
            name="Update Older Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("900.00"),
            monthly_contribution=Decimal("90.00"),
        )
        db.session.add_all([auth_fund, older_fund])
        db.session.flush()

        db.session.add_all([
            AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"),
            AccountMember(user_id=older_user.id, account_id=older_fund.id, role="owner"),
        ])
        db.session.flush()

        foreign_goal = Goal(
            user_id=older_user.id,
            savings_fund_id=older_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("20.00"),
            is_completed=False,
        )
        db.session.add(foreign_goal)
        db.session.commit()

        foreign_goal_id = str(foreign_goal.id)
        original_target_amount = foreign_goal.target_amount

    resp = auth_client.patch(
        f"/api/goals/{foreign_goal_id}",
        json={"target_amount": "150.00"},
    )

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Goal not found"

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(foreign_goal_id))
        assert goal is not None
        assert goal.target_amount == original_target_amount


def test_goals_allocate_allows_authenticated_owner_to_update_own_goal(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        auth_fund = SavingsFund(
            name="Allocate Auth Fund",
            balance=Decimal("400.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        db.session.add(auth_fund)
        db.session.flush()

        db.session.add(AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"))
        db.session.flush()

        auth_goal = Goal(
            user_id=auth_user.id,
            savings_fund_id=auth_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("20.00"),
            is_completed=False,
        )
        db.session.add(auth_goal)
        db.session.commit()

        auth_goal_id = str(auth_goal.id)

    resp = auth_client.post(
        f"/api/goals/{auth_goal_id}/allocate",
        json={"delta_amount": "30.00"},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"]["id"] == auth_goal_id
    assert body["data"]["current_amount"] == 50.0

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(auth_goal_id))
        assert goal is not None
        assert goal.current_amount == Decimal("50.00")


def test_goals_allocate_rejects_foreign_goal_for_authenticated_user(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        older_user = create_user_with_main_account(
            username=f"older_{uuid.uuid4().hex[:8]}",
            email=f"older_{uuid.uuid4().hex[:8]}@test.local",
            password_hash="hash",
            is_verified=True,
        )
        db.session.flush()

        auth_fund = SavingsFund(
            name="Allocate Auth Fund",
            balance=Decimal("400.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        older_fund = SavingsFund(
            name="Allocate Older Fund",
            balance=Decimal("400.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("900.00"),
            monthly_contribution=Decimal("90.00"),
        )
        db.session.add_all([auth_fund, older_fund])
        db.session.flush()

        db.session.add_all([
            AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"),
            AccountMember(user_id=older_user.id, account_id=older_fund.id, role="owner"),
        ])
        db.session.flush()

        foreign_goal = Goal(
            user_id=older_user.id,
            savings_fund_id=older_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("20.00"),
            is_completed=False,
        )
        db.session.add(foreign_goal)
        db.session.commit()

        foreign_goal_id = str(foreign_goal.id)
        original_current_amount = foreign_goal.current_amount

    resp = auth_client.post(
        f"/api/goals/{foreign_goal_id}/allocate",
        json={"delta_amount": "30.00"},
    )

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Goal not found"

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(foreign_goal_id))
        assert goal is not None
        assert goal.current_amount == original_current_amount


def test_goals_complete_allows_authenticated_owner_to_complete_own_goal(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        auth_fund = SavingsFund(
            name="Complete Auth Fund",
            balance=Decimal("400.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        db.session.add(auth_fund)
        db.session.flush()

        db.session.add(AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"))
        db.session.flush()

        auth_goal = Goal(
            user_id=auth_user.id,
            savings_fund_id=auth_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("120.00"),
            is_completed=False,
        )
        db.session.add(auth_goal)
        db.session.commit()

        auth_goal_id = str(auth_goal.id)
        original_balance = auth_fund.balance

    resp = auth_client.post(f"/api/goals/{auth_goal_id}/complete")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"]["id"] == auth_goal_id
    assert body["data"]["is_completed"] is True

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(auth_goal_id))
        fund = db.session.get(SavingsFund, goal.savings_fund_id)
        assert goal is not None
        assert goal.is_completed is True
        assert fund is not None
        assert fund.balance == original_balance - Decimal("120.00")


def test_goals_complete_rejects_foreign_goal_for_authenticated_user(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        older_user = create_user_with_main_account(
            username=f"older_{uuid.uuid4().hex[:8]}",
            email=f"older_{uuid.uuid4().hex[:8]}@test.local",
            password_hash="hash",
            is_verified=True,
        )
        db.session.flush()

        auth_fund = SavingsFund(
            name="Complete Auth Fund",
            balance=Decimal("400.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        older_fund = SavingsFund(
            name="Complete Older Fund",
            balance=Decimal("400.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("900.00"),
            monthly_contribution=Decimal("90.00"),
        )
        db.session.add_all([auth_fund, older_fund])
        db.session.flush()

        db.session.add_all([
            AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"),
            AccountMember(user_id=older_user.id, account_id=older_fund.id, role="owner"),
        ])
        db.session.flush()

        foreign_goal = Goal(
            user_id=older_user.id,
            savings_fund_id=older_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("120.00"),
            is_completed=False,
        )
        db.session.add(foreign_goal)
        db.session.commit()

        foreign_goal_id = str(foreign_goal.id)
        original_balance = older_fund.balance

    resp = auth_client.post(f"/api/goals/{foreign_goal_id}/complete")

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Goal not found"

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(foreign_goal_id))
        fund = db.session.get(SavingsFund, goal.savings_fund_id)
        assert goal is not None
        assert goal.is_completed is False
        assert fund is not None
        assert fund.balance == original_balance


def test_goals_reopen_allows_authenticated_owner_to_reopen_own_goal(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        auth_fund = SavingsFund(
            name="Reopen Auth Fund",
            balance=Decimal("280.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        db.session.add(auth_fund)
        db.session.flush()

        db.session.add(AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"))
        db.session.flush()

        auth_goal = Goal(
            user_id=auth_user.id,
            savings_fund_id=auth_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("120.00"),
            is_completed=True,
        )
        db.session.add(auth_goal)
        db.session.commit()

        auth_goal_id = str(auth_goal.id)
        original_balance = auth_fund.balance

    resp = auth_client.post(f"/api/goals/{auth_goal_id}/reopen")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"]["id"] == auth_goal_id
    assert body["data"]["is_completed"] is False

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(auth_goal_id))
        fund = db.session.get(SavingsFund, goal.savings_fund_id)
        assert goal is not None
        assert goal.is_completed is False
        assert fund is not None
        assert fund.balance == original_balance + Decimal("120.00")


def test_goals_reopen_rejects_foreign_goal_for_authenticated_user(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        older_user = create_user_with_main_account(
            username=f"older_{uuid.uuid4().hex[:8]}",
            email=f"older_{uuid.uuid4().hex[:8]}@test.local",
            password_hash="hash",
            is_verified=True,
        )
        db.session.flush()

        auth_fund = SavingsFund(
            name="Reopen Auth Fund",
            balance=Decimal("400.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        older_fund = SavingsFund(
            name="Reopen Older Fund",
            balance=Decimal("280.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("900.00"),
            monthly_contribution=Decimal("90.00"),
        )
        db.session.add_all([auth_fund, older_fund])
        db.session.flush()

        db.session.add_all([
            AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"),
            AccountMember(user_id=older_user.id, account_id=older_fund.id, role="owner"),
        ])
        db.session.flush()

        foreign_goal = Goal(
            user_id=older_user.id,
            savings_fund_id=older_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("120.00"),
            is_completed=True,
        )
        db.session.add(foreign_goal)
        db.session.commit()

        foreign_goal_id = str(foreign_goal.id)
        original_balance = older_fund.balance

    resp = auth_client.post(f"/api/goals/{foreign_goal_id}/reopen")

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Goal not found"

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(foreign_goal_id))
        fund = db.session.get(SavingsFund, goal.savings_fund_id)
        assert goal is not None
        assert goal.is_completed is True
        assert fund is not None
        assert fund.balance == original_balance


def test_goals_delete_allows_authenticated_owner_to_delete_own_goal(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        auth_fund = SavingsFund(
            name="Delete Auth Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        db.session.add(auth_fund)
        db.session.flush()

        db.session.add(AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"))
        db.session.flush()

        auth_goal = Goal(
            user_id=auth_user.id,
            savings_fund_id=auth_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("0.00"),
            is_completed=False,
        )
        db.session.add(auth_goal)
        db.session.commit()

        auth_goal_id = str(auth_goal.id)

    resp = auth_client.delete(f"/api/goals/{auth_goal_id}")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"] == {"id": auth_goal_id}

    with app.app_context():
        assert db.session.get(Goal, uuid.UUID(auth_goal_id)) is None


def test_goals_delete_rejects_foreign_goal_for_authenticated_user(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        older_user = create_user_with_main_account(
            username=f"older_{uuid.uuid4().hex[:8]}",
            email=f"older_{uuid.uuid4().hex[:8]}@test.local",
            password_hash="hash",
            is_verified=True,
        )
        db.session.flush()

        auth_fund = SavingsFund(
            name="Delete Auth Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        older_fund = SavingsFund(
            name="Delete Older Fund",
            balance=Decimal("0.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("900.00"),
            monthly_contribution=Decimal("90.00"),
        )
        db.session.add_all([auth_fund, older_fund])
        db.session.flush()

        db.session.add_all([
            AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"),
            AccountMember(user_id=older_user.id, account_id=older_fund.id, role="owner"),
        ])
        db.session.flush()

        foreign_goal = Goal(
            user_id=older_user.id,
            savings_fund_id=older_fund.id,
            target_amount=Decimal("120.00"),
            current_amount=Decimal("0.00"),
            is_completed=False,
        )
        db.session.add(foreign_goal)
        db.session.commit()

        foreign_goal_id = str(foreign_goal.id)
        older_user_id = older_user.id

    resp = auth_client.delete(f"/api/goals/{foreign_goal_id}")

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Goal not found"

    with app.app_context():
        goal = db.session.get(Goal, uuid.UUID(foreign_goal_id))
        assert goal is not None
        assert goal.user_id == older_user_id


def test_savings_funds_delete_cascades_receipts(auth_client, app):
    with app.app_context():
        auth_user = _get_user("u@test.local")

        auth_fund = SavingsFund(
            name="Receipt-backed Fund",
            balance=Decimal("80.00"),
            currency="EUR",
            account_type="savings_fund",
            target_amount=Decimal("500.00"),
            monthly_contribution=Decimal("50.00"),
        )
        db.session.add(auth_fund)
        db.session.flush()

        db.session.add(AccountMember(user_id=auth_user.id, account_id=auth_fund.id, role="owner"))
        db.session.flush()

        receipt = Receipt(
            user_id=auth_user.id,
            account_id=auth_fund.id,
            description="Fund expense",
            issue_date=date(2025, 1, 15),
            total_amount=Decimal("12.50"),
            external_uid=None,
            extra_metadata=None,
        )
        db.session.add(receipt)
        db.session.commit()

        auth_fund_id = str(auth_fund.id)
        receipt_id = str(receipt.id)

    resp = auth_client.delete(f"/api/savings-funds/{auth_fund_id}")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"] == {"id": auth_fund_id}

    with app.app_context():
        assert db.session.get(SavingsFund, uuid.UUID(auth_fund_id)) is None
        assert db.session.get(Receipt, uuid.UUID(receipt_id)) is None


def test_import_qr_preview_ok(client):
    payload = {"payload": [{"OPD": "sample", "date": "2025-10-10", "item": "Mlieko", "qnt": "1", "price": "1.20"}]}
    r = client.post("/api/import-qr/preview", json=payload)
    data = assert_json_ok(r)
    assert "items" in data
    assert "count" in data
    assert data["count"] == len(data["items"])


def test_import_qr_extract_id_missing_image_uses_structured_error(auth_client):
    resp = auth_client.post("/api/import-qr/extract-id")

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Missing image file"


def test_import_qr_extract_id_invalid_extension_uses_structured_error(auth_client):
    resp = auth_client.post(
        "/api/import-qr/extract-id",
        data={"image": (io.BytesIO(b"fake-image"), "receipt.txt")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Invalid file type. Please upload an image."


def test_import_qr_extract_id_rate_limit_uses_structured_error(auth_client):
    from app.api import importqr

    remote_addr = "203.0.113.10"
    key = f"{remote_addr}:api_importqr_extract_id"
    importqr.rate_limit_store[key] = [time.time()] * 10

    try:
        resp = auth_client.post(
            "/api/import-qr/extract-id",
            data={"image": (io.BytesIO(b"fake-image"), "receipt.png")},
            content_type="multipart/form-data",
            environ_overrides={"REMOTE_ADDR": remote_addr},
        )
    finally:
        importqr.rate_limit_store.pop(key, None)

    assert resp.status_code == 429
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "rate_limit_exceeded"
    assert body["error"]["message"] == "Rate limit exceeded. Try again later."


def test_auth_flow_ok(client):
    reg = client.post("/api/auth/register", json={"email": "u@test.local", "password": "pass"})
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": "u@test.local", "password": "pass"})
    assert_json_ok(login)
    me = client.get("/api/auth/me")
    me_data = assert_json_ok(me)
    assert me_data["email"] == "u@test.local"
    logout = client.post("/api/auth/logout")
    assert_json_ok(logout)


@pytest.mark.parametrize("path", [
    "/api/export/csv?year=2025&month=10",
    "/api/export/pdf?year=2025&month=10",
])
def test_export_ok(app, auth_client, path):
    with app.app_context():
        user = _get_user("u@test.local")
        account = _get_main_account(user)
        groceries = Category(user_id=user.id, name="Groceries", limit=Decimal("99.00"))
        db.session.add(groceries)
        db.session.flush()

        income = Income(
            user_id=user.id,
            description="Salary",
            amount=Decimal("1000.00"),
            income_date=date(2025, 10, 1),
        )
        receipt_with_item = Receipt(
            user_id=user.id,
            account_id=account.id,
            description="Store receipt",
            issue_date=date(2025, 10, 2),
            total_amount=Decimal("12.34"),
        )
        receipt_without_item = Receipt(
            user_id=user.id,
            account_id=account.id,
            description="Parking",
            issue_date=date(2025, 10, 3),
            total_amount=Decimal("5.00"),
        )
        db.session.add_all([income, receipt_with_item, receipt_without_item])
        db.session.flush()

        db.session.add(
            ReceiptItem(
                receipt_id=receipt_with_item.id,
                user_id=user.id,
                category_id=groceries.id,
                name="Bread",
                quantity=Decimal("1"),
                unit_price=Decimal("12.34"),
                total_price=Decimal("12.34"),
            )
        )
        db.session.commit()

    r = auth_client.get(path)
    assert r.status_code == 200
    assert len(r.data) > 0

    if path.endswith("csv?year=2025&month=10"):
        csv_body = r.data.decode("utf-8")
        assert "Salary" in csv_body
        assert "Bread" in csv_body
        assert "Parking" in csv_body
        assert "Groceries" in csv_body


def test_export_pdf_invalid_month_returns_bad_request(auth_client):
    r = auth_client.get("/api/export/pdf?year=2025&month=13")

    assert r.status_code == 400
    assert r.is_json
    body = r.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Month must be between 1 and 12"


def test_app_does_not_register_legacy_services_container(app):
    assert "services" not in app.extensions


def test_private_api_requires_auth(client):
    r = client.get("/api/incomes")
    assert r.status_code == 401
    assert r.is_json
    body = r.get_json()
    assert body["error"]["code"] == "unauthenticated"


def test_incomes_list_rejects_out_of_range_year_with_400(client):
    client.post("/api/auth/register", json={"email": "year-range@test.local", "password": "pass"})
    client.post("/api/auth/login", json={"email": "year-range@test.local", "password": "pass"})

    r = client.get("/api/incomes", query_string={"year": 10000, "month": 1})

    assert r.status_code == 400
    assert r.is_json
    body = r.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Invalid year format"


def test_incomes_list_rejects_invalid_sort_field(auth_client):
    r = auth_client.get("/api/incomes", query_string={"sort": "description"})

    assert r.status_code == 400
    assert r.is_json
    body = r.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Invalid sort field"


def test_create_income_non_object_json_uses_error_envelope(auth_client):
    r = auth_client.post("/api/incomes", json=["not", "an", "object"])

    assert r.status_code == 400
    assert r.is_json
    body = r.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "JSON body must be an object"


def test_create_income_allows_empty_string_tag_id_as_no_tag(auth_client):
    r = auth_client.post(
        "/api/incomes",
        json={
            "income_date": "2025-10-10",
            "description": "Salary",
            "amount": 1000,
            "tag_id": "",
        },
    )

    assert r.status_code == 201
    assert r.is_json
    body = r.get_json()
    assert body["error"] is None
    created_id = body["data"]["id"]

    details = auth_client.get(f"/api/incomes/{created_id}")
    assert details.status_code == 200
    details_body = details.get_json()
    assert details_body["error"] is None
    assert details_body["data"]["tag_id"] is None


def test_update_income_treats_empty_string_tag_id_as_detach(auth_client):
    created = auth_client.post(
        "/api/incomes",
        json={
            "income_date": "2025-10-10",
            "description": "Salary",
            "amount": 1000,
        },
    )
    assert created.status_code == 201
    income_id = created.get_json()["data"]["id"]

    r = auth_client.put(
        f"/api/incomes/{income_id}",
        json={"tag_id": ""},
    )

    assert r.status_code == 200
    assert r.is_json
    body = r.get_json()
    assert body["error"] is None

    details = auth_client.get(f"/api/incomes/{income_id}")
    assert details.status_code == 200
    details_body = details.get_json()
    assert details_body["error"] is None
    assert details_body["data"]["tag_id"] is None


def test_user_cannot_access_another_users_income(client, app):
    client.post("/api/auth/register", json={"email": "first@test.local", "password": "pass"})
    client.post("/api/auth/login", json={"email": "first@test.local", "password": "pass"})
    created = client.post(
        "/api/incomes",
        json={
            "income_date": "2025-10-10",
            "description": "Salary",
            "amount": 1000,
        },
    )
    assert created.status_code == 201
    income_id = created.get_json()["data"]["id"]
    client.post("/api/auth/logout")

    other = app.test_client()
    other.post("/api/auth/register", json={"email": "second@test.local", "password": "pass"})
    other.post("/api/auth/login", json={"email": "second@test.local", "password": "pass"})
    resp = other.get(f"/api/incomes/{income_id}")
    assert resp.status_code == 404


def test_receipts_list_rejects_invalid_sort_field(auth_client):
    r = auth_client.get("/api/receipts", query_string={"sort": "description"})

    assert r.status_code == 400
    assert r.is_json
    body = r.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Invalid sort field"


def test_create_receipt_uses_authenticated_user_not_payload_user_id(client, app):
    client.post("/api/auth/register", json={"email": "receipt-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-owner@test.local")
        other = _get_user("receipt-other@test.local")

    login = client.post("/api/auth/login", json={"email": "receipt-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.post(
        "/api/receipts",
        json={
            "user_id": str(other.id),
            "description": "Owner purchase",
            "issue_date": "2025-10-10",
            "total_amount": 25.5,
        },
    )

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["error"] is None
    created_id = uuid.UUID(body["data"]["id"])

    with app.app_context():
        receipt = db.session.get(Receipt, created_id)
        assert receipt is not None
        assert receipt.user_id == owner.id
        assert receipt.user_id != other.id


def test_create_receipt_account_id_allows_owned_account_and_rejects_foreign_account(client, app):
    client.post("/api/auth/register", json={"email": "receipt-account-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-account-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-account-owner@test.local")
        other = _get_user("receipt-account-other@test.local")
        owner_account = _get_main_account(owner)
        other_account = _get_main_account(other)
        owner_account_id = str(owner_account.id)
        other_account_id = str(other_account.id)

    login = client.post("/api/auth/login", json={"email": "receipt-account-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    allowed = client.post(
        "/api/receipts",
        json={
            "account_id": owner_account_id,
            "description": "Owner account purchase",
            "issue_date": "2025-10-10",
            "total_amount": 25.5,
        },
    )
    assert allowed.status_code == 201
    allowed_body = allowed.get_json()
    assert allowed_body["error"] is None

    denied = client.post(
        "/api/receipts",
        json={
            "account_id": other_account_id,
            "description": "Foreign account purchase",
            "issue_date": "2025-10-10",
            "total_amount": 30,
        },
    )
    assert denied.status_code == 403
    denied_body = denied.get_json()
    assert denied_body["data"] is None
    assert denied_body["error"]["code"] == "forbidden"
    assert denied_body["error"]["message"] == "User is not a member of this account"


def test_create_receipt_tag_id_allows_owned_tag_and_rejects_foreign_tag(client, app):
    client.post("/api/auth/register", json={"email": "receipt-tag-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-tag-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-tag-owner@test.local")
        other = _get_user("receipt-tag-other@test.local")
        owner_tag = Tag(user_id=owner.id, name="Owner tag")
        foreign_tag = Tag(user_id=other.id, name="Foreign tag")
        db.session.add_all([owner_tag, foreign_tag])
        db.session.commit()
        owner_tag_id = str(owner_tag.id)
        foreign_tag_id = str(foreign_tag.id)

    login = client.post("/api/auth/login", json={"email": "receipt-tag-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    allowed = client.post(
        "/api/receipts",
        json={
            "tag_id": owner_tag_id,
            "description": "Owned tag purchase",
            "issue_date": "2025-10-10",
            "total_amount": 25.5,
        },
    )
    assert allowed.status_code == 201
    allowed_body = allowed.get_json()
    assert allowed_body["error"] is None
    allowed_receipt_id = uuid.UUID(allowed_body["data"]["id"])

    with app.app_context():
        receipt = db.session.get(Receipt, allowed_receipt_id)
        assert receipt is not None
        assert str(receipt.tag_id) == owner_tag_id

    denied = client.post(
        "/api/receipts",
        json={
            "tag_id": foreign_tag_id,
            "description": "Foreign tag purchase",
            "issue_date": "2025-10-10",
            "total_amount": 30,
        },
    )
    assert denied.status_code == 403
    denied_body = denied.get_json()
    assert denied_body["data"] is None
    assert denied_body["error"]["code"] == "forbidden"
    assert denied_body["error"]["message"] == "Tag does not belong to this user"


def test_receipts_list_is_scoped_to_authenticated_user(client, app):
    client.post("/api/auth/register", json={"email": "receipt-list-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-list-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-list-owner@test.local")
        other = _get_user("receipt-list-other@test.local")
        owner_account = _get_main_account(owner)
        other_account = _get_main_account(other)

        owner_receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Owner receipt",
            issue_date=date(2025, 5, 10),
            total_amount=Decimal("20.00"),
        )
        other_receipt = Receipt(
            user_id=other.id,
            account_id=other_account.id,
            description="Other receipt",
            issue_date=date(2025, 5, 11),
            total_amount=Decimal("40.00"),
        )
        db.session.add_all([owner_receipt, other_receipt])
        db.session.commit()
        owner_receipt_id = str(owner_receipt.id)
        other_receipt_id = str(other_receipt.id)

    login = client.post("/api/auth/login", json={"email": "receipt-list-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.get("/api/receipts")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None

    receipt_ids = {item["id"] for item in body["data"]}
    assert owner_receipt_id in receipt_ids
    assert other_receipt_id not in receipt_ids


def test_receipts_list_account_filter_allows_owned_account_and_rejects_foreign_account(client, app):
    client.post("/api/auth/register", json={"email": "receipt-filter-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-filter-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-filter-owner@test.local")
        other = _get_user("receipt-filter-other@test.local")
        owner_account = _get_main_account(owner)
        other_account = _get_main_account(other)

        owner_receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Owner filtered receipt",
            issue_date=date(2025, 5, 12),
            total_amount=Decimal("15.00"),
        )
        db.session.add(owner_receipt)
        db.session.commit()

        owner_account_id = str(owner_account.id)
        other_account_id = str(other_account.id)
        owner_receipt_id = str(owner_receipt.id)

    login = client.post("/api/auth/login", json={"email": "receipt-filter-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    allowed = client.get("/api/receipts", query_string={"account_id": owner_account_id})
    assert allowed.status_code == 200
    allowed_body = allowed.get_json()
    assert allowed_body["error"] is None
    assert [item["id"] for item in allowed_body["data"]] == [owner_receipt_id]

    denied = client.get("/api/receipts", query_string={"account_id": other_account_id})
    assert denied.status_code == 403
    denied_body = denied.get_json()
    assert denied_body["data"] is None
    assert denied_body["error"]["code"] == "forbidden"
    assert denied_body["error"]["message"] == "User is not a member of this account"


def test_user_cannot_access_another_users_receipt(client, app):
    client.post("/api/auth/register", json={"email": "receipt-first@test.local", "password": "pass"})
    client.post("/api/auth/login", json={"email": "receipt-first@test.local", "password": "pass"})
    created = client.post(
        "/api/receipts",
        json={
            "description": "Salary",
            "issue_date": "2025-10-10",
            "total_amount": 20,
        },
    )
    assert created.status_code == 201
    receipt_id = created.get_json()["data"]["id"]
    client.post("/api/auth/logout")

    other = app.test_client()
    other.post("/api/auth/register", json={"email": "receipt-second@test.local", "password": "pass"})
    other.post("/api/auth/login", json={"email": "receipt-second@test.local", "password": "pass"})
    resp = other.get(f"/api/receipts/{receipt_id}")
    assert resp.status_code == 404


def test_receipt_items_list_returns_items_for_authenticated_receipt_owner(client, app):
    client.post("/api/auth/register", json={"email": "receipt-items-owner@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-items-owner@test.local")
        owner_account = _get_main_account(owner)
        receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Groceries",
            issue_date=date(2025, 5, 10),
            total_amount=Decimal("8.50"),
        )
        db.session.add(receipt)
        db.session.flush()

        item = ReceiptItem(
            receipt_id=receipt.id,
            user_id=owner.id,
            name="Milk",
            quantity=Decimal("2.000"),
            unit_price=Decimal("1.75"),
            total_price=Decimal("3.50"),
            extra_metadata={"brand": "Test"},
        )
        db.session.add(item)
        db.session.commit()

        receipt_id = str(receipt.id)
        item_id = str(item.id)
        owner_id = str(owner.id)

    login = client.post("/api/auth/login", json={"email": "receipt-items-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.get(f"/api/receipts/{receipt_id}/items")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"] == [{
        "id": item_id,
        "receipt_id": receipt_id,
        "user_id": owner_id,
        "category_id": None,
        "name": "Milk",
        "quantity": 2.0,
        "unit_price": 1.75,
        "total_price": 3.5,
        "extra_metadata": {"brand": "Test"},
    }]


def test_receipt_items_list_rejects_foreign_receipt_with_standard_not_found_envelope(client, app):
    client.post("/api/auth/register", json={"email": "receipt-items-requester@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-items-owner2@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-items-owner2@test.local")
        owner_account = _get_main_account(owner)
        receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Foreign receipt",
            issue_date=date(2025, 5, 11),
            total_amount=Decimal("4.20"),
        )
        db.session.add(receipt)
        db.session.commit()
        foreign_receipt_id = str(receipt.id)

    login = client.post("/api/auth/login", json={"email": "receipt-items-requester@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.get(f"/api/receipts/{foreign_receipt_id}/items")

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Receipt not found"


def test_receipt_items_create_creates_item_for_authenticated_receipt_owner(client, app):
    client.post("/api/auth/register", json={"email": "receipt-items-create@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-items-create@test.local")
        owner_account = _get_main_account(owner)
        receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Create item target",
            issue_date=date(2025, 5, 12),
            total_amount=Decimal("0.00"),
        )
        db.session.add(receipt)
        db.session.commit()
        receipt_id = str(receipt.id)
        owner_id = owner.id

    login = client.post("/api/auth/login", json={"email": "receipt-items-create@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.post(
        f"/api/receipts/{receipt_id}/items",
        json={"name": "Bread", "quantity": 2, "unit_price": 1.25},
    )

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"]["message"] == "Item created successfully"
    item_id = uuid.UUID(body["data"]["item_id"])

    with app.app_context():
        item = db.session.get(ReceiptItem, item_id)
        assert item is not None
        assert item.receipt_id == uuid.UUID(receipt_id)
        assert item.user_id == owner_id
        assert item.name == "Bread"
        assert float(item.total_price) == 2.5


def test_receipt_items_create_rejects_foreign_receipt_with_standard_not_found_envelope(client, app):
    client.post("/api/auth/register", json={"email": "receipt-items-create-requester@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-items-create-owner@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-items-create-owner@test.local")
        owner_account = _get_main_account(owner)
        receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Foreign create receipt",
            issue_date=date(2025, 5, 13),
            total_amount=Decimal("0.00"),
        )
        db.session.add(receipt)
        db.session.commit()
        foreign_receipt_id = str(receipt.id)

    login = client.post("/api/auth/login", json={"email": "receipt-items-create-requester@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.post(
        f"/api/receipts/{foreign_receipt_id}/items",
        json={"name": "Bread", "quantity": 1, "unit_price": 1.25},
    )

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Receipt not found"


def test_receipt_items_create_rejects_foreign_category_with_standard_not_found_envelope(client, app):
    client.post("/api/auth/register", json={"email": "receipt-items-category-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-items-category-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-items-category-owner@test.local")
        other = _get_user("receipt-items-category-other@test.local")
        owner_account = _get_main_account(owner)
        receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Category guard",
            issue_date=date(2025, 5, 14),
            total_amount=Decimal("0.00"),
        )
        foreign_category = Category(user_id=other.id, name="Foreign receipt item category")
        db.session.add_all([receipt, foreign_category])
        db.session.commit()
        receipt_id = str(receipt.id)
        foreign_category_id = str(foreign_category.id)

    login = client.post("/api/auth/login", json={"email": "receipt-items-category-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.post(
        f"/api/receipts/{receipt_id}/items",
        json={"name": "Bread", "quantity": 1, "unit_price": 1.25, "category_id": foreign_category_id},
    )

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Category not found"


def test_receipt_items_update_rejects_foreign_item_with_standard_not_found_envelope(client, app):
    client.post("/api/auth/register", json={"email": "receipt-items-update-requester@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-items-update-owner@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-items-update-owner@test.local")
        owner_account = _get_main_account(owner)
        receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Foreign update receipt",
            issue_date=date(2025, 5, 15),
            total_amount=Decimal("5.00"),
        )
        db.session.add(receipt)
        db.session.flush()
        item = ReceiptItem(
            receipt_id=receipt.id,
            user_id=owner.id,
            name="Milk",
            quantity=Decimal("1.000"),
            unit_price=Decimal("2.00"),
            total_price=Decimal("2.00"),
        )
        db.session.add(item)
        db.session.commit()
        foreign_receipt_id = str(receipt.id)
        foreign_item_id = str(item.id)

    login = client.post("/api/auth/login", json={"email": "receipt-items-update-requester@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.put(
        f"/api/receipts/{foreign_receipt_id}/items/{foreign_item_id}",
        json={"name": "Updated"},
    )

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Receipt not found"


def test_receipt_items_delete_rejects_foreign_item_with_standard_not_found_envelope(client, app):
    client.post("/api/auth/register", json={"email": "receipt-items-delete-requester@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "receipt-items-delete-owner@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-items-delete-owner@test.local")
        owner_account = _get_main_account(owner)
        receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Foreign delete receipt",
            issue_date=date(2025, 5, 16),
            total_amount=Decimal("5.00"),
        )
        db.session.add(receipt)
        db.session.flush()
        item = ReceiptItem(
            receipt_id=receipt.id,
            user_id=owner.id,
            name="Cheese",
            quantity=Decimal("1.000"),
            unit_price=Decimal("3.00"),
            total_price=Decimal("3.00"),
        )
        db.session.add(item)
        db.session.commit()
        foreign_receipt_id = str(receipt.id)
        foreign_item_id = str(item.id)

    login = client.post("/api/auth/login", json={"email": "receipt-items-delete-requester@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.delete(f"/api/receipts/{foreign_receipt_id}/items/{foreign_item_id}")

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Receipt not found"


def test_update_receipt_rejects_wrong_type_issue_date_with_standard_bad_request_envelope(client, app):
    client.post("/api/auth/register", json={"email": "receipt-update-invalid@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("receipt-update-invalid@test.local")
        owner_account = _get_main_account(owner)
        receipt = Receipt(
            user_id=owner.id,
            account_id=owner_account.id,
            description="Update target",
            issue_date=date(2025, 5, 10),
            total_amount=Decimal("20.00"),
        )
        db.session.add(receipt)
        db.session.commit()
        receipt_id = receipt.id

    login = client.post("/api/auth/login", json={"email": "receipt-update-invalid@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.put(
        f"/api/receipts/{receipt_id}",
        json={"issue_date": 123},
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Invalid issue_date format, expected YYYY-MM-DD"

    with app.app_context():
        receipt = db.session.get(Receipt, receipt_id)
        assert receipt is not None
        assert receipt.issue_date == date(2025, 5, 10)


def test_receipts_ekasa_items_rejects_foreign_account_filter(client, app):
    client.post("/api/auth/register", json={"email": "ekasa-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "ekasa-other@test.local", "password": "pass"})

    with app.app_context():
        other = _get_user("ekasa-other@test.local")
        other_account = _get_main_account(other)
        foreign_account_id = str(other_account.id)

    login = client.post("/api/auth/login", json={"email": "ekasa-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.get(
        "/api/receipts/ekasa-items",
        query_string={"year": 2025, "month": 5, "account_id": foreign_account_id},
    )

    assert resp.status_code == 403
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "forbidden"
    assert body["error"]["message"] == "User is not a member of this account"


def test_import_receipt_from_ekasa_rejects_legacy_camel_case_request_fields(client):
    client.post("/api/auth/register", json={"email": "ekasa-import@test.local", "password": "pass"})
    login = client.post("/api/auth/login", json={"email": "ekasa-import@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.post(
        "/api/receipts/import-ekasa",
        json={
            "receiptId": "1234567890ABCDEF",
        },
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Missing receipt_id"


def test_ekasa_service_raises_upstream_service_error_on_non_200(monkeypatch):
    class DummyResponse:
        status_code = 503

        def json(self):
            return {}

    monkeypatch.setattr(ekasa_service.requests, "post", lambda *args, **kwargs: DummyResponse())

    with pytest.raises(UpstreamServiceError, match="eKasa API returned 503"):
        ekasa_service.fetch_receipt_data("1234567890ABCDEF")


def test_ekasa_service_raises_upstream_service_error_on_invalid_json(monkeypatch):
    class DummyResponse:
        status_code = 200

        def json(self):
            raise ValueError("not json")

    monkeypatch.setattr(ekasa_service.requests, "post", lambda *args, **kwargs: DummyResponse())

    with pytest.raises(UpstreamServiceError, match="Invalid response returned by eKasa API"):
        ekasa_service.fetch_receipt_data("1234567890ABCDEF")


def test_import_receipt_from_ekasa_propagates_ekasa_upstream_errors_in_standard_envelope(client, monkeypatch):
    client.post("/api/auth/register", json={"email": "ekasa-failure@test.local", "password": "pass"})
    login = client.post("/api/auth/login", json={"email": "ekasa-failure@test.local", "password": "pass"})
    assert login.status_code == 200

    def raise_ekasa_error(receipt_id):
        raise UpstreamServiceError("eKasa API returned 503")

    monkeypatch.setattr(ekasa_service, "fetch_receipt_data", raise_ekasa_error)

    resp = client.post(
        "/api/receipts/import-ekasa",
        json={
            "receipt_id": "1234567890ABCDEF",
        },
    )

    assert resp.status_code == 502
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "upstream_service_error"
    assert body["error"]["message"] == "eKasa API returned 503"


def test_categories_list_is_scoped_to_current_user_and_shared_categories(client, app):
    client.post("/api/auth/register", json={"email": "owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("owner@test.local")
        other = _get_user("other@test.local")
        db.session.add_all([
            Category(user_id=owner.id, name="Owner category", count=2),
            Category(user_id=other.id, name="Other category", count=5),
            Category(user_id=None, name="Shared category", count=1),
        ])
        db.session.commit()

    login = client.post("/api/auth/login", json={"email": "owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.get("/api/categories")
    data = assert_json_ok(resp)

    names = {category["name"] for category in data["categories"]}
    shared_category = next(category for category in data["categories"] if category["name"] == "Shared category")
    assert "Owner category" in names
    assert "Shared category" in names
    assert "Other category" not in names
    assert shared_category["user_id"] is None


def test_create_category_uses_authenticated_user_not_payload_user_id(client, app):
    client.post("/api/auth/register", json={"email": "owner-create@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "other-create@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("owner-create@test.local")
        other = _get_user("other-create@test.local")

    login = client.post("/api/auth/login", json={"email": "owner-create@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.post(
        "/api/categories",
        json={
            "user_id": str(other.id),
            "name": "Created by owner",
            "limit": 25.5,
            "count": 99,
            "is_pinned": True,
        },
    )

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["error"] is None
    created_id = uuid.UUID(body["data"]["id"])

    with app.app_context():
        category = db.session.get(Category, created_id)
        assert category is not None
        assert category.user_id == owner.id
        assert category.user_id != other.id
        assert category.count == 0
        assert category.is_pinned is False


def test_create_category_rejects_parent_owned_by_another_user(client, app):
    client.post("/api/auth/register", json={"email": "owner-parent@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "other-parent@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("owner-parent@test.local")
        other = _get_user("other-parent@test.local")
        shared_parent = Category(user_id=None, name="Shared parent")
        foreign_parent = Category(user_id=other.id, name="Foreign parent")
        db.session.add_all([shared_parent, foreign_parent])
        db.session.commit()
        shared_parent_id = shared_parent.id
        foreign_parent_id = foreign_parent.id
        owner_id = owner.id

    login = client.post("/api/auth/login", json={"email": "owner-parent@test.local", "password": "pass"})
    assert login.status_code == 200

    allowed = client.post(
        "/api/categories",
        json={"name": "Child of shared", "parent_id": str(shared_parent_id)},
    )
    assert allowed.status_code == 201

    denied = client.post(
        "/api/categories",
        json={"name": "Child of foreign", "parent_id": str(foreign_parent_id)},
    )
    assert denied.status_code == 404
    denied_body = denied.get_json()
    assert denied_body["data"] is None
    assert denied_body["error"]["code"] == "not_found"
    assert denied_body["error"]["message"] == "Parent category not found"

    with app.app_context():
        created = db.session.query(Category).filter(Category.name == "Child of shared").one()
        assert created.user_id == owner_id
        assert created.parent_id == shared_parent_id


def test_create_category_missing_json_uses_error_envelope(auth_client):
    resp = auth_client.post(
        "/api/categories",
        data="not-json",
        content_type="text/plain",
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Missing JSON body"


def test_create_category_non_object_json_uses_error_envelope(auth_client):
    resp = auth_client.post("/api/categories", json=["not", "an", "object"])

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "JSON body must be an object"


def test_category_monthly_limit_is_scoped_to_current_user(client, app):
    client.post("/api/auth/register", json={"email": "limit-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "limit-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("limit-owner@test.local")
        other = _get_user("limit-other@test.local")

        owner_account = _get_main_account(owner)
        other_account = _get_main_account(other)

        owner_category = Category(user_id=owner.id, name="Owner limit", limit=Decimal("250.00"))
        other_category = Category(user_id=other.id, name="Other limit", limit=Decimal("400.00"))
        db.session.add_all([owner_category, other_category])
        db.session.flush()

        other_receipt = Receipt(
            user_id=other.id,
            account_id=other_account.id,
            description="Other purchase",
            issue_date=date(2025, 5, 10),
            total_amount=Decimal("60.00"),
        )
        db.session.add(other_receipt)
        db.session.flush()

        db.session.add(
            ReceiptItem(
                receipt_id=other_receipt.id,
                user_id=other.id,
                category_id=other_category.id,
                name="Hidden item",
                quantity=Decimal("1"),
                unit_price=Decimal("60.00"),
                total_price=Decimal("60.00"),
            )
        )
        db.session.commit()

        owner_category_id = owner_category.id
        other_category_id = other_category.id
        owner_account_id = owner_account.id
        owner_id = owner.id

    login = client.post("/api/auth/login", json={"email": "limit-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    own_resp = client.get(
        f"/api/categories/monthly-limit?year=2025&month=5&category_id={owner_category_id}"
    )
    assert own_resp.status_code == 200
    own_body = own_resp.get_json()
    assert own_body["error"] is None
    assert own_body["data"]["category_id"] == str(owner_category_id)
    assert own_body["data"]["spent"] == 0.0
    assert own_body["data"]["limit"] == 250.0

    foreign_resp = client.get(
        f"/api/categories/monthly-limit?year=2025&month=5&category_id={other_category_id}"
    )
    assert foreign_resp.status_code == 404
    foreign_body = foreign_resp.get_json()
    assert foreign_body["data"] is None
    assert foreign_body["error"]["code"] == "not_found"
    assert foreign_body["error"]["message"] == "Category not found"

    with app.app_context():
        owner_receipt = Receipt(
            user_id=owner_id,
            account_id=owner_account_id,
            description="Owner purchase",
            issue_date=date(2025, 5, 11),
            total_amount=Decimal("35.00"),
        )
        db.session.add(owner_receipt)
        db.session.flush()
        db.session.add(
            ReceiptItem(
                receipt_id=owner_receipt.id,
                user_id=owner_id,
                category_id=owner_category_id,
                name="Visible item",
                quantity=Decimal("1"),
                unit_price=Decimal("35.00"),
                total_price=Decimal("35.00"),
            )
        )
        db.session.commit()

    updated_resp = client.get(
        f"/api/categories/monthly-limit?year=2025&month=5&category_id={owner_category_id}"
    )
    assert updated_resp.status_code == 200
    updated_body = updated_resp.get_json()
    assert updated_body["error"] is None
    assert updated_body["data"]["spent"] == 35.0


def test_category_monthly_limit_rejects_out_of_range_year(auth_client):
    with auth_client.application.app_context():
        user = _get_user("u@test.local")
        category = Category(user_id=user.id, name="Year limited")
        db.session.add(category)
        db.session.commit()
        category_id = category.id

    resp = auth_client.get(
        f"/api/categories/monthly-limit?year=10000&month=5&category_id={category_id}"
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Invalid year format"


def test_update_category_allows_owner_to_update_own_category(client, app):
    client.post("/api/auth/register", json={"email": "update-owner@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("update-owner@test.local")
        category = Category(user_id=owner.id, name="Original", count=1, is_pinned=False, limit=Decimal("10.00"))
        db.session.add(category)
        db.session.commit()
        category_id = category.id

    login = client.post("/api/auth/login", json={"email": "update-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.put(
        f"/api/categories/{category_id}",
        json={"name": "Updated", "count": 7, "is_pinned": True, "limit": 25.5},
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"]["message"] == "Category updated successfully"

    with app.app_context():
        category = db.session.get(Category, category_id)
        assert category.name == "Updated"
        assert category.count == 7
        assert category.is_pinned is True
        assert category.limit == Decimal("25.5")


def test_update_category_rejects_foreign_category_with_standard_not_found_envelope(client, app):
    client.post("/api/auth/register", json={"email": "update-foreign-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "update-foreign-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("update-foreign-owner@test.local")
        other = _get_user("update-foreign-other@test.local")
        foreign_category = Category(user_id=other.id, name="Foreign update target", count=2)
        db.session.add(foreign_category)
        db.session.commit()
        foreign_category_id = foreign_category.id
        owner_id = owner.id
        other_id = other.id

    login = client.post("/api/auth/login", json={"email": "update-foreign-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.put(
        f"/api/categories/{foreign_category_id}",
        json={"name": "Hijacked"},
    )

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Category not found"

    with app.app_context():
        category = db.session.get(Category, foreign_category_id)
        assert category is not None
        assert category.user_id == other_id
        assert category.user_id != owner_id
        assert category.name == "Foreign update target"


def test_update_category_invalid_input_uses_standard_bad_request_envelope(client, app):
    client.post("/api/auth/register", json={"email": "update-invalid@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("update-invalid@test.local")
        category = Category(user_id=owner.id, name="Invalid input target", count=1)
        db.session.add(category)
        db.session.commit()
        category_id = category.id

    login = client.post("/api/auth/login", json={"email": "update-invalid@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.put(
        f"/api/categories/{category_id}",
        json={"count": "not-a-number"},
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Invalid input data"

    with app.app_context():
        category = db.session.get(Category, category_id)
        assert category.count == 1


def test_update_category_rejects_blank_name_and_preserves_existing_name(client, app):
    client.post("/api/auth/register", json={"email": "update-blank@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("update-blank@test.local")
        category = Category(user_id=owner.id, name="Still valid", count=1)
        db.session.add(category)
        db.session.commit()
        category_id = category.id

    login = client.post("/api/auth/login", json={"email": "update-blank@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.put(
        f"/api/categories/{category_id}",
        json={"name": "   "},
    )

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Missing name"

    with app.app_context():
        category = db.session.get(Category, category_id)
        assert category.name == "Still valid"


def test_delete_category_allows_owner_to_delete_own_category(client, app):
    client.post("/api/auth/register", json={"email": "delete-owner@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("delete-owner@test.local")
        category = Category(user_id=owner.id, name="Delete me")
        db.session.add(category)
        db.session.commit()
        category_id = category.id

    login = client.post("/api/auth/login", json={"email": "delete-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.delete(f"/api/categories/{category_id}")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error"] is None
    assert body["data"]["message"] == "Category deleted successfully"

    with app.app_context():
        assert db.session.get(Category, category_id) is None


def test_delete_category_rejects_foreign_category_with_standard_not_found_envelope(client, app):
    client.post("/api/auth/register", json={"email": "delete-foreign-owner@test.local", "password": "pass"})
    client.post("/api/auth/register", json={"email": "delete-foreign-other@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("delete-foreign-owner@test.local")
        other = _get_user("delete-foreign-other@test.local")
        foreign_category = Category(user_id=other.id, name="Foreign delete target")
        db.session.add(foreign_category)
        db.session.commit()
        foreign_category_id = foreign_category.id
        other_id = other.id

    login = client.post("/api/auth/login", json={"email": "delete-foreign-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.delete(f"/api/categories/{foreign_category_id}")

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Category not found"

    with app.app_context():
        category = db.session.get(Category, foreign_category_id)
        assert category is not None
        assert category.user_id == other_id


def test_delete_category_rejects_shared_parent_and_preserves_child_categories(client, app):
    client.post("/api/auth/register", json={"email": "shared-delete-owner@test.local", "password": "pass"})

    with app.app_context():
        owner = _get_user("shared-delete-owner@test.local")
        shared_parent = Category(user_id=None, name="Shared delete target")
        db.session.add(shared_parent)
        db.session.flush()
        child = Category(user_id=owner.id, parent_id=shared_parent.id, name="Child survives")
        db.session.add(child)
        db.session.commit()
        shared_parent_id = shared_parent.id
        child_id = child.id

    login = client.post("/api/auth/login", json={"email": "shared-delete-owner@test.local", "password": "pass"})
    assert login.status_code == 200

    resp = client.delete(f"/api/categories/{shared_parent_id}")

    assert resp.status_code == 404
    body = resp.get_json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Category not found"

    with app.app_context():
        assert db.session.get(Category, shared_parent_id) is not None
        assert db.session.get(Category, child_id) is not None


def test_app_creates_successfully(app):
    """Test that the application factory creates an app instance."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_database_connection(app):
    """Test that database connection is established."""
    with app.app_context():
        assert db.engine is not None


def test_database_tables_created(app):
    """Test that database tables are created successfully."""
    with app.app_context():
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        assert len(tables) > 0


def test_database_seeder_compatibility(monkeypatch):
    """Ensure the database seeder matches the current schema.

    This test fails when the schema changes without a corresponding update to
    the seeder, signaling that the seeding logic must be revised.
    """
    monkeypatch.setenv("APP_ENV", "test")
    seed_main()


def test_app_context_works(app):
    """Test that Flask application context functions correctly."""
    with app.app_context():
        assert app.config is not None
        assert app.extensions is not None


def test_app_env_is_test(app):
    """Test that the Flask app uses the test configuration."""
    assert app.config["TESTING"] is True
