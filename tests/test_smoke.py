import os
import pytest
from budget_app.app import create_app

class TestCfg:
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test"
    DEFAULT_CURRENCY = "EUR"

@pytest.fixture
def client():
    os.environ["APP_ENV"] = "test"
    app = create_app(TestCfg)
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
    r = client.get("/api/goals")
    data = assert_json_ok(r)
    assert "items" in data
    assert "count" in data

def test_dashboard_ok(client):
    r = client.get("/api/dashboard?month=2025-10")
    data = assert_json_ok(r)
    assert data.get("month") == "2025-10"
    for k in ["total_exp", "total_inc", "sections", "cats_exp", "months", "series_inc", "series_exp"]:
        assert k in data

def test_import_qr_preview_ok(client):
    payload = {"payload": [{"OPD": "sample", "date": "2025-10-10", "item": "Mlieko", "qnt": "1", "price": "1.20"}]}
    r = client.post("/api/import-qr/preview", json=payload)
    data = assert_json_ok(r)
    assert "items" in data
    assert "count" in data
    assert data["count"] == len(data["items"])

def test_auth_flow_ok(client):
    reg = client.post("/api/auth/register", json={"email": "u@test.local", "password": "pass"})
    assert reg.status_code in (200, 201)
    login = client.post("/api/auth/login", json={"email": "u@test.local", "password": "pass"})
    body = login.get_json()
    if login.status_code != 200:
        assert "error" in body and body["error"] is None
    else:
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
