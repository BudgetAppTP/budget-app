from app.extensions import db
from app.models import Tag


def user_id(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    return response.get_json()["data"]["id"]


def create_tag(client, name, tag_type=None):
    payload = {"name": name}
    if tag_type:
        payload["type"] = tag_type
    response = client.post("/api/tags", json=payload)
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def create_income(client, tag_id=None):
    payload = {"description": "Tagged income", "amount": 10, "income_date": "2025-10-10"}
    if tag_id:
        payload["tag_id"] = tag_id
    response = client.post("/api/incomes", json=payload)
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def create_receipt(client, tag_id=None):
    payload = {"description": "Tagged receipt", "total_amount": 10, "issue_date": "2025-10-10"}
    if tag_id:
        payload["tag_id"] = tag_id
    response = client.post("/api/receipts", json=payload)
    assert response.status_code == 201
    return response.get_json()["data"]["id"]


def test_category_create_rejects_missing_name_and_invalid_parent(auth_client_factory):
    client = auth_client_factory("category-validation@test.local")

    missing_name = client.post("/api/categories", json={})
    invalid_parent = client.post("/api/categories", json={"name": "Food", "parent_id": "not-a-uuid"})

    assert missing_name.status_code == 400
    assert invalid_parent.status_code == 400


def test_create_tag_rejects_empty_name_and_invalid_type(auth_client_factory):
    client = auth_client_factory("tag-validation@test.local")

    empty_name = client.post("/api/tags", json={"name": "   "})
    invalid_type = client.post("/api/tags", json={"name": "Bad type", "type": "invalid"})

    assert empty_name.status_code == 400
    assert invalid_type.status_code == 400


def test_duplicate_tag_name_for_same_user_reuses_existing_tag(auth_client_factory, app):
    client = auth_client_factory("tag-duplicate@test.local")

    first_id = create_tag(client, "Salary", "income")
    second = client.post("/api/tags", json={"name": "Salary", "type": "income"})

    assert second.status_code == 201
    assert second.get_json()["data"]["id"] == first_id
    with app.app_context():
        assert db.session.query(Tag).filter_by(name="Salary").count() == 1


def test_same_tag_name_can_exist_for_different_users(auth_client_factory, app):
    first = auth_client_factory("tag-first@test.local")
    second = auth_client_factory("tag-second@test.local")

    first_id = create_tag(first, "Shared name", "income")
    second_id = create_tag(second, "Shared name", "income")

    assert first_id != second_id
    with app.app_context():
        assert db.session.query(Tag).filter_by(name="Shared name").count() == 2


def test_user_cannot_list_update_or_delete_another_users_tags(auth_client_factory):
    owner = auth_client_factory("tag-owner@test.local")
    other = auth_client_factory("tag-other@test.local")
    tag_id = create_tag(owner, "Private income tag", "income")

    other_tags = other.get("/api/tags/income").get_json()["data"]["tags"]
    update = other.put(f"/api/tags/{tag_id}", json={"name": "Changed"})
    delete = other.delete(f"/api/tags/{tag_id}")

    assert tag_id not in {tag["id"] for tag in other_tags}
    assert update.status_code == 404
    assert delete.status_code == 404


def test_request_payload_user_id_is_ignored_for_tag_creation(auth_client_factory):
    owner = auth_client_factory("tag-payload-owner@test.local")
    other = auth_client_factory("tag-payload-other@test.local")
    owner_id = user_id(owner)
    other_id = user_id(other)

    response = owner.post("/api/tags", json={"user_id": other_id, "name": "Owned by auth", "type": "income"})

    assert response.status_code == 201
    tags = owner.get("/api/tags/income").get_json()["data"]["tags"]
    created = next(tag for tag in tags if tag["id"] == response.get_json()["data"]["id"])
    assert created["user_id"] == owner_id


def test_tag_counters_increment_and_decrement_for_income_and_receipt_assignments(auth_client_factory):
    client = auth_client_factory("tag-counters@test.local")
    tag_id = create_tag(client, "Flexible")

    income_id = create_income(client, tag_id=tag_id)
    receipt_id = create_receipt(client, tag_id=tag_id)
    both_tags = client.get("/api/tags/income").get_json()["data"]["tags"]
    tag_after_assign = next(tag for tag in both_tags if tag["id"] == tag_id)
    assert tag_after_assign["counter"] == 2
    assert tag_after_assign["type"] == "both"

    client.put(f"/api/incomes/{income_id}", json={"tag_id": None})
    expense_tags = client.get("/api/tags/expense").get_json()["data"]["tags"]
    tag_after_income_unassign = next(tag for tag in expense_tags if tag["id"] == tag_id)
    assert tag_after_income_unassign["counter"] == 1
    assert tag_after_income_unassign["type"] == "expense"

    client.delete(f"/api/receipts/{receipt_id}")
    assert tag_id not in {tag["id"] for tag in client.get("/api/tags/income").get_json()["data"]["tags"]}
    assert tag_id not in {tag["id"] for tag in client.get("/api/tags/expense").get_json()["data"]["tags"]}


def test_income_and_expense_tag_endpoints_filter_by_type(auth_client_factory):
    client = auth_client_factory("tag-filter@test.local")
    income_tag = create_tag(client, "Income only")
    expense_tag = create_tag(client, "Expense only")
    both_tag = create_tag(client, "Both")

    create_income(client, tag_id=income_tag)
    create_receipt(client, tag_id=expense_tag)
    create_income(client, tag_id=both_tag)
    create_receipt(client, tag_id=both_tag)

    income_ids = {tag["id"] for tag in client.get("/api/tags/income").get_json()["data"]["tags"]}
    expense_ids = {tag["id"] for tag in client.get("/api/tags/expense").get_json()["data"]["tags"]}

    assert income_tag in income_ids
    assert both_tag in income_ids
    assert expense_tag not in income_ids
    assert expense_tag in expense_ids
    assert both_tag in expense_ids
    assert income_tag not in expense_ids
