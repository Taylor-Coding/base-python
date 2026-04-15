import pytest
from fastapi.testclient import TestClient

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REFRESH_URL = "/api/auth/refresh"
LOGOUT_URL = "/api/auth/logout"


@pytest.fixture
def registered_user(client: TestClient):
    client.post(REGISTER_URL, json={"email": "auth@example.com", "password": "password123"})
    return {"email": "auth@example.com", "password": "password123"}


def test_login_success(client: TestClient, registered_user):
    response = client.post(LOGIN_URL, json=registered_user)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in response.cookies


def test_login_wrong_password(client: TestClient, registered_user):
    response = client.post(LOGIN_URL, json={"email": registered_user["email"], "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(client: TestClient):
    response = client.post(LOGIN_URL, json={"email": "nobody@example.com", "password": "password123"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"


def test_login_sets_is_first_login_false(client: TestClient):
    client.post(REGISTER_URL, json={"email": "first@example.com", "password": "password123"})
    login_res = client.post(LOGIN_URL, json={"email": "first@example.com", "password": "password123"})
    assert login_res.status_code == 200

    token = login_res.json()["access_token"]
    me_res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["is_first_login"] is False


def test_refresh_issues_new_access_token(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    assert login_res.status_code == 200

    refresh_res = client.post(REFRESH_URL)
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in refresh_res.cookies


def test_refresh_rotates_refresh_token(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    original_cookie = login_res.cookies.get("refresh_token")

    refresh_res = client.post(REFRESH_URL)
    new_cookie = refresh_res.cookies.get("refresh_token")

    assert new_cookie is not None
    assert new_cookie != original_cookie


def test_refresh_without_cookie_returns_401(client: TestClient):
    client.cookies.clear()
    response = client.post(REFRESH_URL)
    assert response.status_code == 401
    assert response.json()["error_code"] == "MISSING_TOKEN"


def test_logout_clears_cookie(client: TestClient, registered_user):
    client.post(LOGIN_URL, json=registered_user)
    assert "refresh_token" in client.cookies

    response = client.post(LOGOUT_URL)
    assert response.status_code == 204
    assert "refresh_token" not in client.cookies


def test_access_token_grants_me_endpoint(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    token = login_res.json()["access_token"]

    me_res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == registered_user["email"]


def test_users_endpoint_blocked_without_token(client: TestClient):
    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert response.json()["error_code"] == "MISSING_TOKEN"
