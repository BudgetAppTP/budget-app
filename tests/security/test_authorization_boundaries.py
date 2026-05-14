from uuid import UUID

from app.extensions import db
from app.models import Category


def user_id(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    return response.get_json()["data"]["id"]


def create_income(client, amount, description, income_date="2025-10-10"):
    response = client.post(
        "/api/incomes",
        json={
            "income_date": income_date,
            "description": description,
            "amount": amount,
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def test_category_payload_user_id_is_ignored_and_categories_are_user_scoped(auth_client_factory, app):
    owner = auth_client_factory("category-owner@test.local")
    other = auth_client_factory("category-other@test.local")
    owner_id = user_id(owner)
    other_id = user_id(other)

    created = owner.post(
        "/api/categories",
        json={"user_id": other_id, "name": "Private category", "limit": 125},
    )
    assert created.status_code == 201
    category_id = created.get_json()["data"]["id"]

    with app.app_context():
        category = db.session.get(Category, UUID(category_id))
        assert str(category.user_id) == owner_id

    owner_categories = owner.get("/api/categories").get_json()["data"]["categories"]
    other_categories = other.get("/api/categories").get_json()["data"]["categories"]
    assert category_id in {category["id"] for category in owner_categories}
    assert category_id not in {category["id"] for category in other_categories}

    update = other.put(f"/api/categories/{category_id}", json={"name": "Stolen"})
    delete = other.delete(f"/api/categories/{category_id}")
    monthly_limit = other.get(f"/api/categories/monthly-limit?year=2025&month=10&category_id={category_id}")

    assert update.status_code == 404
    assert delete.status_code == 404
    assert monthly_limit.status_code == 404


def test_monthly_budget_ignores_user_id_query_parameter(auth_client_factory):
    owner = auth_client_factory("budget-owner@test.local")
    other = auth_client_factory("budget-other@test.local")
    other_id = user_id(other)

    create_income(owner, amount=50, description="Owner salary")
    create_income(other, amount=200, description="Other salary")

    response = owner.get(f"/api/monthly-budget?year=2025&month=10&user_id={other_id}")

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["total_income"] == 50.0
    assert [income["description"] for income in data["incomes"]] == ["Owner salary"]
