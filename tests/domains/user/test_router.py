import pytest
from fastapi.testclient import TestClient

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"


def test_register_user(client: TestClient):
    response = client.post(
        REGISTER_URL,
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data


def test_register_duplicate_email(client: TestClient):
    payload = {"email": "dup@example.com", "password": "password123"}
    client.post(REGISTER_URL, json=payload)
    response = client.post(REGISTER_URL, json=payload)
    assert response.status_code == 409


def test_get_me(client: TestClient):
    client.post(REGISTER_URL, json={"email": "me@example.com", "password": "password123"})
    login_res = client.post(LOGIN_URL, json={"email": "me@example.com", "password": "password123"})
    token = login_res.json()["access_token"]

    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
