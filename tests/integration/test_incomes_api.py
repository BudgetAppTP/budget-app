def create_income(client, description, amount, income_date):
    response = client.post(
        "/api/incomes",
        json={"description": description, "amount": amount, "income_date": income_date},
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def income_descriptions(response):
    assert response.status_code == 200
    return [item["description"] for item in response.get_json()["data"]["incomes"]]


def test_user_cannot_update_or_delete_another_users_income(auth_client_factory):
    owner = auth_client_factory("income-owner@test.local")
    other = auth_client_factory("income-other@test.local")
    income_id = create_income(owner, "Owner salary", 100, "2025-10-10")

    update = other.put(f"/api/incomes/{income_id}", json={"description": "Changed"})
    delete = other.delete(f"/api/incomes/{income_id}")

    assert update.status_code == 404
    assert delete.status_code == 404
    assert owner.get(f"/api/incomes/{income_id}").status_code == 200


def test_create_income_validates_description_date_and_amount(auth_client_factory):
    client = auth_client_factory("income-validation@test.local")

    missing_description = client.post("/api/incomes", json={"amount": 10, "income_date": "2025-10-10"})
    invalid_date = client.post(
        "/api/incomes",
        json={"description": "Bad date", "amount": 10, "income_date": "not-a-date"},
    )
    invalid_amount = client.post(
        "/api/incomes",
        json={"description": "Bad amount", "amount": "not-a-number", "income_date": "2025-10-10"},
    )

    assert missing_description.status_code == 400
    assert invalid_date.status_code == 400
    assert invalid_amount.status_code == 400


def test_list_incomes_filters_by_month_and_rejects_partial_month_filter(auth_client_factory):
    client = auth_client_factory("income-filter@test.local")
    create_income(client, "October salary", 100, "2025-10-10")
    create_income(client, "November salary", 200, "2025-11-10")

    october = client.get("/api/incomes?year=2025&month=10")
    year_only = client.get("/api/incomes?year=2025")
    month_only = client.get("/api/incomes?month=10")

    assert income_descriptions(october) == ["October salary"]
    assert year_only.status_code == 400
    assert month_only.status_code == 400


def test_list_incomes_sorts_by_date_and_amount_in_both_directions(auth_client_factory):
    client = auth_client_factory("income-sort@test.local")
    create_income(client, "Middle", 20, "2025-10-10")
    create_income(client, "First", 10, "2025-10-01")
    create_income(client, "Last", 30, "2025-10-20")

    assert income_descriptions(client.get("/api/incomes?sort=income_date&order=asc")) == ["First", "Middle", "Last"]
    assert income_descriptions(client.get("/api/incomes?sort=income_date&order=desc")) == ["Last", "Middle", "First"]
    assert income_descriptions(client.get("/api/incomes?sort=amount&order=asc")) == ["First", "Middle", "Last"]
    assert income_descriptions(client.get("/api/incomes?sort=amount&order=desc")) == ["Last", "Middle", "First"]


def test_update_income_rejects_empty_description(auth_client_factory):
    client = auth_client_factory("income-update-validation@test.local")
    income_id = create_income(client, "Valid", 10, "2025-10-10")

    response = client.put(f"/api/incomes/{income_id}", json={"description": "   "})

    assert response.status_code == 400


def test_delete_income_removes_record(auth_client_factory):
    client = auth_client_factory("income-delete@test.local")
    income_id = create_income(client, "Temporary", 10, "2025-10-10")

    delete = client.delete(f"/api/incomes/{income_id}")
    read_after_delete = client.get(f"/api/incomes/{income_id}")

    assert delete.status_code == 200
    assert read_after_delete.status_code == 404
