from uuid import UUID

import pytest

from app.extensions import db
from app.models import Receipt


def user_id(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    return response.get_json()["data"]["id"]


def create_receipt(client, **overrides):
    payload = {"description": "Receipt", "total_amount": 20, "issue_date": "2025-10-10"}
    payload.update(overrides)
    response = client.post("/api/receipts", json=payload)
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def create_item(client, receipt_id, **overrides):
    payload = {"name": "Milk", "quantity": 2, "unit_price": 1.5}
    payload.update(overrides)
    response = client.post(f"/api/receipts/{receipt_id}/items", json=payload)
    assert response.status_code == 201
    return response.get_json()["data"]["item_id"]


def test_request_payload_user_id_is_ignored_for_receipt_creation(auth_client_factory, app):
    owner = auth_client_factory("receipt-payload-owner@test.local")
    other = auth_client_factory("receipt-payload-other@test.local")
    owner_id = user_id(owner)
    other_id = user_id(other)

    receipt_id = create_receipt(owner, user_id=other_id)

    with app.app_context():
        receipt = db.session.get(Receipt, UUID(receipt_id))
        assert str(receipt.user_id) == owner_id


def test_user_cannot_access_update_or_delete_another_users_receipt(auth_client_factory):
    owner = auth_client_factory("receipt-owner@test.local")
    other = auth_client_factory("receipt-other@test.local")
    receipt_id = create_receipt(owner)

    read = other.get(f"/api/receipts/{receipt_id}")
    update = other.put(f"/api/receipts/{receipt_id}", json={"description": "Changed"})
    delete = other.delete(f"/api/receipts/{receipt_id}")

    assert read.status_code == 404
    assert update.status_code == 404
    assert delete.status_code == 404


def test_receipt_create_and_update_validation(auth_client_factory):
    client = auth_client_factory("receipt-validation@test.local")
    receipt_id = create_receipt(client)

    missing_body = client.post("/api/receipts", json={})
    missing_description = client.post("/api/receipts", json={"total_amount": 1, "issue_date": "2025-10-10"})
    invalid_date = client.post("/api/receipts", json={"description": "Bad", "issue_date": "invalid"})
    empty_update = client.put(f"/api/receipts/{receipt_id}", json={"description": " "})

    assert missing_body.status_code == 400
    assert missing_description.status_code == 400
    assert invalid_date.status_code == 400
    assert empty_update.status_code == 400


def test_user_cannot_access_update_or_delete_another_users_receipt_items(auth_client_factory):
    owner = auth_client_factory("item-owner@test.local")
    other = auth_client_factory("item-other@test.local")
    receipt_id = create_receipt(owner)
    item_id = create_item(owner, receipt_id)

    list_items = other.get(f"/api/receipts/{receipt_id}/items")
    create_on_receipt = other.post(f"/api/receipts/{receipt_id}/items", json={"name": "Bread", "quantity": 1, "unit_price": 2})
    update = other.put(f"/api/receipts/{receipt_id}/items/{item_id}", json={"name": "Changed"})
    delete = other.delete(f"/api/receipts/{receipt_id}/items/{item_id}")

    assert list_items.status_code == 404
    assert create_on_receipt.status_code == 404
    assert update.status_code == 404
    assert delete.status_code == 404


def test_receipt_item_create_and_update_validation(auth_client_factory):
    client = auth_client_factory("item-validation@test.local")
    receipt_id = create_receipt(client)
    item_id = create_item(client, receipt_id)

    missing_body = client.post(f"/api/receipts/{receipt_id}/items", json={})
    invalid_quantity = client.post(f"/api/receipts/{receipt_id}/items", json={"name": "Bad", "quantity": "x", "unit_price": 1})
    invalid_update = client.put(f"/api/receipts/{receipt_id}/items/{item_id}", json={"quantity": "x"})

    assert missing_body.status_code == 400
    assert invalid_quantity.status_code == 400
    assert invalid_update.status_code == 400


@pytest.mark.xfail(reason="Goals are currently global in-memory records and have no user ownership field.")
def test_user_cannot_access_another_users_goals(auth_client_factory):
    owner = auth_client_factory("goal-owner@test.local")
    other = auth_client_factory("goal-other@test.local")

    created = owner.post("/api/goals", json={"name": "Private goal", "type": "saving", "target_amount": 100})
    assert created.status_code == 201
    goal_id = created.get_json()["data"]["id"]

    other_goals = other.get("/api/goals").get_json()["data"]["items"]
    assert goal_id not in {goal["id"] for goal in other_goals}


@pytest.mark.skip(reason="No financial-target API endpoints exist yet; only the database model is present.")
def test_user_cannot_access_another_users_financial_targets():
    pass
