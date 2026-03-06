"""
Smoke tests for the Budget Tracker application.

These tests verify that the application can start and basic infrastructure works.
"""
import os
import uuid
import pytest

from app import create_app
from app.extensions import db
from scripts.seed import main as seed_main


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app()

    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    return app.test_client()


def assert_json_ok(resp):
    assert resp.status_code == 200
    assert resp.is_json
    body = resp.get_json()
    assert "data" in body
    assert "error" in body and body["error"] is None
    return body["data"]


def test_health_ok(client):
    r = client.get("/api/health")
    data = assert_json_ok(r)
    assert data.get("status") == "ok"


def test_transactions_list_ok(client):
    r = client.get("/api/transactions")
    data = assert_json_ok(r)
    assert "items" in data
    assert "count" in data
    assert isinstance(data["items"], list)


def test_budgets_get_ok(client):
    r = client.get("/api/budgets?month=2025-10")
    data = assert_json_ok(r)
    assert data.get("month") == "2025-10"
    assert "items" in data
    assert "left" in data


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
        headers=headers,
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


def test_dashboard_ok(client):
    r = client.get("/api/dashboard/summary?year=2025&month=10")
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


def test_import_qr_preview_ok(client):
    payload = {"payload": [{"OPD": "sample", "date": "2025-10-10", "item": "Mlieko", "qnt": "1", "price": "1.20"}]}
    r = client.post("/api/import-qr/preview", json=payload)
    data = assert_json_ok(r)
    assert "items" in data
    assert "count" in data
    assert data["count"] == len(data["items"])


def test_auth_flow_ok(client):
    reg = client.post("/api/auth/register", json={"email": "u@test.local", "password": "pass"})
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": "u@test.local", "password": "pass"})
    assert_json_ok(login)
    logout = client.post("/api/auth/logout")
    assert_json_ok(logout)


@pytest.mark.parametrize("path", [
    "/api/export/csv?month=2025-10",
    "/api/export/pdf?month=2025-10",
])
def test_export_ok(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert len(r.data) > 0


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


def test_database_seeder_compatibility():
    """Ensure the database seeder matches the current schema.

    This test fails when the schema changes without a corresponding update to
    the seeder, signaling that the seeding logic must be revised.
    """
    seed_main()


def test_app_context_works(app):
    """Test that Flask application context functions correctly."""
    with app.app_context():
        assert app.config is not None
        assert app.extensions is not None


def test_app_env_is_test():
    """Test that APP_ENV environment variable is set to 'test'."""
    app_env = os.getenv("APP_ENV", "").lower()
    assert app_env == "test", (
        f"APP_ENV must be set to 'test' for tests to run safely. "
        f"Current value: '{app_env}'. Check pytest.ini configuration."
    )
