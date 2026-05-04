from datetime import date


def create_income(client, amount, income_date=None):
    response = client.post(
        "/api/incomes",
        json={
            "description": "Income",
            "amount": amount,
            "income_date": income_date or date.today().isoformat(),
        },
    )
    assert response.status_code == 201


def create_receipt(client, amount, issue_date=None):
    response = client.post(
        "/api/receipts",
        json={
            "description": "Receipt",
            "total_amount": amount,
            "issue_date": issue_date or date.today().isoformat(),
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def test_monthly_budget_defaults_to_current_month(auth_client_factory):
    client = auth_client_factory("monthly-default@test.local")
    create_income(client, 75)

    response = client.get("/api/monthly-budget")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["month"] == date.today().strftime("%Y-%m")
    assert data["total_income"] == 75.0


def test_monthly_budget_rejects_invalid_month_format(auth_client_factory):
    client = auth_client_factory("monthly-invalid@test.local")

    response = client.get("/api/monthly-budget?month=2025-13")

    assert response.status_code == 400


def test_monthly_budget_totals_income_and_expenses(auth_client_factory):
    client = auth_client_factory("monthly-totals@test.local")
    create_income(client, 300, "2025-10-01")
    create_receipt(client, 125, "2025-10-02")

    response = client.get("/api/monthly-budget?month=2025-10")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["total_income"] == 300.0
    assert data["total_expense"] == 125.0
    assert data["balance"] == 175.0


def test_dashboard_summary_includes_only_authenticated_users_data(auth_client_factory):
    owner = auth_client_factory("dashboard-owner@test.local")
    other = auth_client_factory("dashboard-other@test.local")
    create_income(owner, 100, "2025-10-01")
    create_receipt(owner, 30, "2025-10-02")
    create_income(other, 900, "2025-10-01")
    create_receipt(other, 400, "2025-10-02")

    response = owner.get("/api/dashboard/summary?year=2025&month=10")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["total_incomes"] == 100.0
    assert data["total_expenses"] == 30.0


def test_dashboard_rejects_invalid_month_and_partial_date(auth_client_factory):
    client = auth_client_factory("dashboard-invalid@test.local")

    invalid_format = client.get("/api/dashboard/summary?year=bad&month=10")
    invalid_month = client.get("/api/dashboard/summary?year=2025&month=13")
    partial = client.get("/api/dashboard/summary?year=2025")

    assert invalid_format.status_code == 400
    assert invalid_month.status_code == 400
    assert partial.status_code == 400


def test_budgets_endpoint_seeds_default_sections_when_empty(auth_client_factory):
    client = auth_client_factory("budgets-seed@test.local")

    response = client.get("/api/budgets?month=2030-01")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["month"] == "2030-01"
    assert len(data["items"]) > 0


def test_budget_update_persists_changed_limit(auth_client_factory):
    client = auth_client_factory("budgets-update@test.local")
    initial = client.get("/api/budgets?month=2030-02").get_json()["data"]
    item = initial["items"][0]

    update = client.put(
        "/api/budgets/2030-02",
        json={"items": [{"id": item["id"], "section": item["section"], "limit_amount": 123.45, "percent_target": 10}]},
    )
    after_update = client.get("/api/budgets?month=2030-02").get_json()["data"]

    assert update.status_code == 200
    changed = next(row for row in after_update["items"] if row["id"] == item["id"])
    assert changed["limit_amount"] == 123.45
