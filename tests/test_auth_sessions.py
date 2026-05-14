from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from uuid import UUID

import pytest

from app import create_app
from app.extensions import db
from app.models import AccountMember, AuthToken, Income
from app.config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


def register_and_login(client, email="user@test.local", password="pass"):
    reg = client.post("/api/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login


def get_cookie_value(response, name):
    cookie = SimpleCookie()
    for header in response.headers.getlist("Set-Cookie"):
        cookie.load(header)
    return cookie[name].value


def test_login_sets_http_only_session_cookie_and_me_uses_it(client):
    login = register_and_login(client)
    set_cookie = login.headers.get("Set-Cookie", "")

    assert "auth_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["data"]["email"] == "user@test.local"


def test_logout_revokes_cookie_session(client):
    register_and_login(client)

    assert client.get("/api/auth/me").status_code == 200
    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert "Max-Age=0" in logout.headers.get("Set-Cookie", "")

    after_logout = client.get("/api/auth/me")
    assert after_logout.status_code == 401
    assert after_logout.get_json()["error"]["code"] == "unauthenticated"


def test_bearer_token_authenticates_and_logout_revokes_it(app):
    password = "pass"
    first = app.test_client()
    login = register_and_login(first, "bearer@test.local", password)
    token = get_cookie_value(login, "auth_token")

    bearer = app.test_client()
    me = bearer.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["data"]["email"] == "bearer@test.local"

    logout = bearer.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 200

    rejected = bearer.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert rejected.status_code == 401


def test_logout_one_session_does_not_revoke_another_session(app):
    password = "pass"
    first = app.test_client()
    second = app.test_client()

    first_login = register_and_login(first, "multi@test.local", password)
    second_login = second.post("/api/auth/login", json={"email": "multi@test.local", "password": password})
    assert second_login.status_code == 200

    first_token = get_cookie_value(first_login, "auth_token")
    second_token = get_cookie_value(second_login, "auth_token")
    assert first_token != second_token

    first.post("/api/auth/logout")

    assert first.get("/api/auth/me").status_code == 401
    assert second.get("/api/auth/me").status_code == 200


def test_expired_session_token_is_rejected_and_removed(app):
    client = app.test_client()
    login = register_and_login(client, "expired@test.local", "pass")
    token = get_cookie_value(login, "auth_token")

    with app.app_context():
        stored = db.session.execute(db.select(AuthToken).filter_by(token=token)).scalar_one()
        stored.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()

    rejected = app.test_client().get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert rejected.status_code == 401

    with app.app_context():
        assert db.session.execute(db.select(AuthToken).filter_by(token=token)).scalar_one_or_none() is None


def test_invalid_login_does_not_create_session_cookie_or_token(client, app):
    client.post("/api/auth/register", json={"email": "bad-login@test.local", "password": "pass"})
    failed = client.post("/api/auth/login", json={"email": "bad-login@test.local", "password": "wrong"})

    assert failed.status_code == 401
    assert "auth_token=" not in failed.headers.get("Set-Cookie", "")

    with app.app_context():
        assert db.session.execute(db.select(AuthToken)).scalars().all() == []


def test_payload_user_id_is_ignored_for_owned_resource_creation(app):
    owner = app.test_client()
    other = app.test_client()

    register_and_login(owner, "owner@test.local", "pass")
    register_and_login(other, "other@test.local", "pass")
    owner_id = owner.get("/api/auth/me").get_json()["data"]["id"]
    other_id = other.get("/api/auth/me").get_json()["data"]["id"]

    created = owner.post(
        "/api/incomes",
        json={
            "user_id": other_id,
            "income_date": "2025-10-10",
            "description": "Must belong to owner",
            "amount": 10,
        },
    )
    assert created.status_code == 201
    income_id = created.get_json()["data"]["id"]

    owner_can_read = owner.get(f"/api/incomes/{income_id}")
    other_cannot_read = other.get(f"/api/incomes/{income_id}")
    assert owner_can_read.status_code == 200
    assert other_cannot_read.status_code == 404

    with app.app_context():
        income = db.session.get(Income, UUID(income_id))
        assert str(income.user_id) == owner_id


def test_account_get_uses_authenticated_session_user(app):
    first = app.test_client()
    second = app.test_client()

    register_and_login(first, "first-account@test.local", "pass")
    register_and_login(second, "second-account@test.local", "pass")

    first_user_id = first.get("/api/auth/me").get_json()["data"]["id"]
    second_user_id = second.get("/api/auth/me").get_json()["data"]["id"]

    with app.app_context():
        first_account = (
            db.session.query(AccountMember)
            .filter(AccountMember.user_id == UUID(first_user_id))
            .first()
        )
        second_account = (
            db.session.query(AccountMember)
            .filter(AccountMember.user_id == UUID(second_user_id))
            .first()
        )

    first_response = first.get("/api/account")
    second_response = second.get("/api/account")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.get_json()["data"]["id"] == str(first_account.account_id)
    assert second_response.get_json()["data"]["id"] == str(second_account.account_id)
    assert first_response.get_json()["data"]["id"] != second_response.get_json()["data"]["id"]


def test_account_patch_updates_only_authenticated_users_main_account(app):
    first = app.test_client()
    second = app.test_client()

    register_and_login(first, "first-account-patch@test.local", "pass")
    register_and_login(second, "second-account-patch@test.local", "pass")

    first_before = first.get("/api/account")
    second_before = second.get("/api/account")
    assert first_before.status_code == 200
    assert second_before.status_code == 200

    first_account_id = first_before.get_json()["data"]["id"]
    second_account_id = second_before.get_json()["data"]["id"]
    assert first_account_id != second_account_id

    renamed = first.patch("/api/account", json={"name": "First patched account"})
    assert renamed.status_code == 200
    assert renamed.get_json()["data"]["id"] == first_account_id
    assert renamed.get_json()["data"]["name"] == "First patched account"

    first_after = first.get("/api/account")
    second_after = second.get("/api/account")
    assert first_after.status_code == 200
    assert second_after.status_code == 200
    assert first_after.get_json()["data"]["id"] == first_account_id
    assert first_after.get_json()["data"]["name"] == "First patched account"
    assert second_after.get_json()["data"]["id"] == second_account_id
    assert second_after.get_json()["data"]["name"] != "First patched account"


def test_account_patch_rejects_missing_json_body(app):
    client = app.test_client()
    register_and_login(client, "account-missing-json@test.local", "pass")

    response = client.patch("/api/account")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "bad_request"
    assert response.get_json()["error"]["message"] == "Missing JSON body"


def test_account_patch_rejects_non_object_json_body(app):
    client = app.test_client()
    register_and_login(client, "account-array-json@test.local", "pass")

    response = client.patch("/api/account", json=["not", "an", "object"])

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "bad_request"
    assert response.get_json()["error"]["message"] == "JSON body must be an object"
