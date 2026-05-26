import pytest
from fastapi.testclient import TestClient

from app.core.clients.redis import cache_delete, cache_get, cache_set, get_redis_client
from app.core.config.settings import settings
from app.core.security.crypto import create_refresh_token, decode_refresh_token
from app.domains.auth.services.auth_service import REFRESH_SESSION_COOKIE


def api_path(path: str) -> str:
    return f"{settings.api_prefix}{path}"


REGISTER_URL = api_path("/auth/register")
LOGIN_URL = api_path("/auth/login")
REFRESH_URL = api_path("/auth/refresh")
LOGOUT_URL = api_path("/auth/logout")
ME_URL = api_path("/users/me")

LOCKOUT_EMAIL = "lockout@example.com"
LOCKOUT_KEY = f"login_lock:{LOCKOUT_EMAIL}"


@pytest.fixture
def lockout_user(client: TestClient):
    client.post(REGISTER_URL, json={"email": LOCKOUT_EMAIL, "password": "correct123"})
    yield {"email": LOCKOUT_EMAIL, "password": "correct123"}
    cache_delete(LOCKOUT_KEY)


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
    assert REFRESH_SESSION_COOKIE in response.cookies
    assert "refresh_token" not in response.cookies


def test_login_wrong_password(client: TestClient, registered_user):
    response = client.post(LOGIN_URL, json={"email": registered_user["email"], "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(client: TestClient):
    response = client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"


def test_unknown_email_is_locked_after_five_failures(client: TestClient):
    payload = {"email": "unknown-lock@example.com", "password": "password123"}

    for _ in range(4):
        response = client.post(LOGIN_URL, json=payload)
        assert response.status_code == 401
        assert response.json()["error_code"] == "INVALID_CREDENTIALS"

    response = client.post(LOGIN_URL, json=payload)

    assert response.status_code == 403
    assert response.json()["error_code"] == "ACCOUNT_LOCKED"


def test_login_sets_is_first_login_false(client: TestClient):
    client.post(REGISTER_URL, json={"email": "first@example.com", "password": "password123"})
    login_res = client.post(
        LOGIN_URL, json={"email": "first@example.com", "password": "password123"}
    )
    assert login_res.status_code == 200

    token = login_res.json()["access_token"]
    me_res = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["is_first_login"] is False


def test_refresh_issues_new_access_token(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    assert login_res.status_code == 200

    refresh_res = client.post(REFRESH_URL)
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert REFRESH_SESSION_COOKIE in refresh_res.cookies
    assert "refresh_token" not in refresh_res.cookies


def test_refresh_rotates_session_key(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    original_cookie = login_res.cookies.get(REFRESH_SESSION_COOKIE)

    refresh_res = client.post(REFRESH_URL)
    new_cookie = refresh_res.cookies.get(REFRESH_SESSION_COOKIE)

    assert new_cookie is not None
    assert new_cookie != original_cookie


def test_refresh_session_stores_metadata(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    session_key = login_res.cookies.get(REFRESH_SESSION_COOKIE)
    assert session_key is not None

    user_id = cache_get(f"refresh_session_lookup:{session_key}")
    session = cache_get(f"refresh_session:{user_id}:{session_key}")
    payload = decode_refresh_token(session["refresh_token"])

    assert session["user_id"] == payload["sub"]
    assert session["jti"] == payload["jti"] == session_key
    assert session["refresh_token"] is not None
    assert session["issued_at"] is not None
    assert session["user_agent_hash"] is not None
    assert session["ip_prefix"] is not None
    assert session["revoked"] is False


def test_refresh_keeps_one_session_per_user(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    original_session_key = login_res.cookies.get(REFRESH_SESSION_COOKIE)
    assert original_session_key is not None
    user_id = cache_get(f"refresh_session_lookup:{original_session_key}")

    refresh_res = client.post(REFRESH_URL)
    new_session_key = refresh_res.cookies.get(REFRESH_SESSION_COOKIE)
    assert new_session_key is not None

    pattern = f"refresh_session:{user_id}:*"
    session_keys = list(get_redis_client().scan_iter(pattern))

    assert cache_get(f"refresh_session:{user_id}:{original_session_key}") is None
    assert cache_get(f"refresh_session_lookup:{original_session_key}") is None
    assert session_keys == [f"refresh_session:{user_id}:{new_session_key}"]


def test_refresh_rejects_reused_session_key(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    original_cookie = login_res.cookies.get(REFRESH_SESSION_COOKIE)
    assert original_cookie is not None

    refresh_res = client.post(REFRESH_URL)
    assert refresh_res.status_code == 200

    client.cookies.set(REFRESH_SESSION_COOKIE, original_cookie)
    reused_res = client.post(REFRESH_URL)

    assert reused_res.status_code == 401
    assert reused_res.json()["error_code"] == "INVALID_TOKEN"


def test_refresh_without_cookie_returns_401(client: TestClient):
    client.cookies.clear()
    response = client.post(REFRESH_URL)
    assert response.status_code == 401
    assert response.json()["error_code"] == "MISSING_TOKEN"


def test_refresh_invalid_subject_returns_401(client: TestClient):
    refresh_token = create_refresh_token("not-a-uuid")
    payload = decode_refresh_token(refresh_token)
    session_key = payload["jti"]
    cache_set(f"refresh_session_lookup:{session_key}", "not-a-uuid")
    cache_set(
        f"refresh_session:not-a-uuid:{session_key}",
        {
            "user_id": "not-a-uuid",
            "jti": session_key,
            "refresh_token": refresh_token,
            "revoked": False,
        },
    )
    client.cookies.set(REFRESH_SESSION_COOKIE, session_key)

    response = client.post(REFRESH_URL)

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"


def test_logout_clears_cookie(client: TestClient, registered_user):
    client.post(LOGIN_URL, json=registered_user)
    assert REFRESH_SESSION_COOKIE in client.cookies

    response = client.post(LOGOUT_URL)
    assert response.status_code == 204
    assert REFRESH_SESSION_COOKIE not in client.cookies

    refresh_res = client.post(REFRESH_URL)
    assert refresh_res.status_code == 401


def test_access_token_grants_me_endpoint(client: TestClient, registered_user):
    login_res = client.post(LOGIN_URL, json=registered_user)
    token = login_res.json()["access_token"]

    me_res = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == registered_user["email"]


def test_users_endpoint_blocked_without_token(client: TestClient):
    response = client.get(ME_URL)
    assert response.status_code == 401
    assert response.json()["error_code"] == "MISSING_TOKEN"


def test_login_failure_under_limit_returns_invalid_credentials(client: TestClient, lockout_user):
    for _ in range(4):
        res = client.post(LOGIN_URL, json={"email": lockout_user["email"], "password": "wrong"})
        assert res.status_code == 401
        assert res.json()["error_code"] == "INVALID_CREDENTIALS"


def test_login_locked_after_five_failures(client: TestClient, lockout_user):
    for _ in range(4):
        client.post(LOGIN_URL, json={"email": lockout_user["email"], "password": "wrong"})

    res = client.post(LOGIN_URL, json={"email": lockout_user["email"], "password": "wrong"})
    assert res.status_code == 403
    assert res.json()["error_code"] == "ACCOUNT_LOCKED"
    assert "5분" in res.json()["message"]


def test_locked_account_blocks_correct_password(client: TestClient, lockout_user):
    for _ in range(5):
        client.post(LOGIN_URL, json={"email": lockout_user["email"], "password": "wrong"})

    res = client.post(
        LOGIN_URL, json={"email": lockout_user["email"], "password": lockout_user["password"]}
    )
    assert res.status_code == 403
    assert res.json()["error_code"] == "ACCOUNT_LOCKED"


def test_login_attempts_reset_on_success(client: TestClient, lockout_user):
    for _ in range(3):
        client.post(LOGIN_URL, json={"email": lockout_user["email"], "password": "wrong"})

    client.post(
        LOGIN_URL, json={"email": lockout_user["email"], "password": lockout_user["password"]}
    )

    res = client.post(LOGIN_URL, json={"email": lockout_user["email"], "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["error_code"] == "INVALID_CREDENTIALS"
