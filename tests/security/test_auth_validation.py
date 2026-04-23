def test_register_rejects_missing_email(client):
    response = client.post("/api/auth/register", json={"password": "pass"})

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "bad_request"


def test_register_rejects_missing_password(client):
    response = client.post("/api/auth/register", json={"email": "missing-password@test.local"})

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "bad_request"


def test_login_rejects_missing_email_or_password(client):
    missing_email = client.post("/api/auth/login", json={"password": "pass"})
    missing_password = client.post("/api/auth/login", json={"email": "missing-password@test.local"})

    assert missing_email.status_code == 401
    assert missing_password.status_code == 401
    assert missing_email.get_json()["error"]["code"] == "auth_failed"
    assert missing_password.get_json()["error"]["code"] == "auth_failed"


def test_login_normalizes_email_case(client):
    registered = client.post("/api/auth/register", json={"email": "MixedCase@Test.Local", "password": "pass"})
    assert registered.status_code == 201

    login = client.post("/api/auth/login", json={"email": "mixedcase@test.local", "password": "pass"})

    assert login.status_code == 200
    assert "auth_token=" in login.headers.get("Set-Cookie", "")


def test_logout_without_token_returns_ok_and_clears_cookie(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.get_json()["data"] == {"ok": True}
    assert "auth_token=" in response.headers.get("Set-Cookie", "")
    assert "Max-Age=0" in response.headers.get("Set-Cookie", "")


def test_invalid_bearer_token_returns_unauthenticated(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthenticated"
