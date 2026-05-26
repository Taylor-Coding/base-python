from fastapi.testclient import TestClient

from app.core.config.settings import settings
from app.core.constants.enums import UserRole
from app.core.security.crypto import create_access_token
from app.domains.user.repositories.user_repository import UserRepository


def api_path(path: str) -> str:
    return f"{settings.api_prefix}{path}"


REGISTER_URL = api_path("/auth/register")
LOGIN_URL = api_path("/auth/login")
ME_URL = api_path("/users/me")
USERS_URL = api_path("/users")


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

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_user_cannot_read_or_update_other_user(client: TestClient):
    owner_res = client.post(
        REGISTER_URL, json={"email": "owner@example.com", "password": "password123"}
    )
    other_res = client.post(
        REGISTER_URL, json={"email": "other@example.com", "password": "password123"}
    )
    login_res = client.post(
        LOGIN_URL, json={"email": "owner@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    other_id = other_res.json()["id"]

    read_res = client.get(f"{USERS_URL}/{other_id}", headers={"Authorization": f"Bearer {token}"})
    update_res = client.patch(
        f"{USERS_URL}/{other_id}",
        json={"name": "blocked"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert owner_res.status_code == 201
    assert read_res.status_code == 403
    assert update_res.status_code == 403


def test_user_cannot_update_own_active_status(client: TestClient):
    client.post(REGISTER_URL, json={"email": "self-status@example.com", "password": "password123"})
    login_res = client.post(
        LOGIN_URL, json={"email": "self-status@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]

    me_res = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    user_id = me_res.json()["id"]

    update_res = client.patch(
        f"{USERS_URL}/{user_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 403
    assert update_res.json()["error_code"] == "FORBIDDEN_ROLE"


def test_admin_can_read_and_delete_user(client: TestClient, db):
    admin_res = client.post(
        REGISTER_URL, json={"email": "admin@example.com", "password": "password123"}
    )
    target_res = client.post(
        REGISTER_URL, json={"email": "target@example.com", "password": "password123"}
    )

    repo = UserRepository(db)
    admin = repo.get_by_email("admin@example.com")
    assert admin is not None
    admin.role = UserRole.ADMIN
    db.flush()

    login_res = client.post(
        LOGIN_URL, json={"email": "admin@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    target_id = target_res.json()["id"]

    read_res = client.get(f"{USERS_URL}/{target_id}", headers={"Authorization": f"Bearer {token}"})
    delete_res = client.delete(
        f"{USERS_URL}/{target_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert admin_res.status_code == 201
    assert read_res.status_code == 200
    assert delete_res.status_code == 204


def test_admin_can_update_user(client: TestClient, db):
    client.post(REGISTER_URL, json={"email": "updater@example.com", "password": "password123"})
    target_res = client.post(
        REGISTER_URL, json={"email": "update-target@example.com", "password": "password123"}
    )

    repo = UserRepository(db)
    admin = repo.get_by_email("updater@example.com")
    assert admin is not None
    admin.role = UserRole.ADMIN
    db.flush()

    login_res = client.post(
        LOGIN_URL, json={"email": "updater@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    target_id = target_res.json()["id"]

    update_res = client.patch(
        f"{USERS_URL}/{target_id}",
        json={"name": "Updated User", "is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated User"
    assert update_res.json()["is_active"] is False


def test_invalid_access_token_subject_returns_401(client: TestClient):
    token = create_access_token("not-a-uuid")

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"
