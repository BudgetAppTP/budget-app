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

@pytest.mark.parametrize("path", [
    "/",
    "/transactions",
    "/transactions/new-income",
    "/transactions/new-expense",
    "/budgets",
    "/goals",
    "/import-qr",
    "/auth/login",
    "/auth/register",
])
def test_pages_ok(client, path):
    r = client.get(path)
    assert r.status_code == 200

@pytest.mark.parametrize("path", [
    "/export/csv?month=2025-10",
    "/export/pdf?month=2025-10",
])
def test_export_ok(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert len(r.data) > 0
