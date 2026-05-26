import math
import uuid
from datetime import datetime, timezone

from fastapi import Request, Response

from app.core.api.exceptions import AppException, AppExceptionCode
from app.core.clients.redis import (
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_keys,
    cache_set,
    redis_expire,
    redis_get_int,
    redis_incr,
    redis_ttl,
)
from app.core.config.settings import settings
from app.core.security.crypto import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
    verify_password,
)
from app.domains.auth.schemas.request import LoginRequest
from app.domains.auth.schemas.response import AccessTokenResponse
from app.domains.user.repositories.user_repository import UserRepository

REFRESH_SESSION_COOKIE = "refresh_session_key"
MAX_LOGIN_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 300  # 5분: 잠금 없이 시도 횟수 유지 기간
LOCKOUT_SECONDS = 300  # 5분: 잠금 지속 시간


def _lock_key(email: str) -> str:
    return f"login_lock:{email}"


def _refresh_key(user_id: str) -> str:
    return f"refresh_session:{user_id}:*"


def _refresh_session_key(user_id: str, jti: str) -> str:
    return f"refresh_session:{user_id}:{jti}"


def _refresh_session_lookup_key(jti: str) -> str:
    return f"refresh_session_lookup:{jti}"


def _ip_prefix(request: Request) -> str | None:
    host = request.client.host if request.client else None
    if not host:
        return None

    if "." in host:
        return ".".join(host.split(".")[:3])

    if ":" in host:
        return ":".join(host.split(":")[:4])

    return host


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def _refresh_ttl_seconds(self) -> int:
        return settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    def _delete_user_refresh_sessions(self, user_id: str) -> None:
        for key in cache_keys(_refresh_key(user_id)):
            session = cache_get(key)
            if session and session.get("jti"):
                cache_delete(_refresh_session_lookup_key(session["jti"]))
        cache_delete_pattern(_refresh_key(user_id))

    def _delete_refresh_session(self, user_id: str, jti: str) -> None:
        cache_delete(_refresh_session_key(user_id, jti))
        cache_delete(_refresh_session_lookup_key(jti))

    def _store_refresh_session(self, refresh_token: str, request: Request) -> str:
        payload = decode_refresh_token(refresh_token)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        if not user_id or not jti:
            raise AppException(AppExceptionCode.INVALID_TOKEN)

        self._delete_user_refresh_sessions(user_id)
        cache_set(
            _refresh_session_key(user_id, jti),
            {
                "user_id": user_id,
                "jti": jti,
                "refresh_token": refresh_token,
                "issued_at": datetime.now(timezone.utc).isoformat(),
                "user_agent_hash": hash_token(request.headers.get("user-agent", "")),
                "ip_prefix": _ip_prefix(request),
                "revoked": False,
            },
            ttl=self._refresh_ttl_seconds(),
        )
        cache_set(_refresh_session_lookup_key(jti), user_id, ttl=self._refresh_ttl_seconds())
        return jti

    def _get_refresh_session(self, session_key: str | None) -> tuple[str, str, dict]:
        if not session_key:
            raise AppException(AppExceptionCode.MISSING_TOKEN)

        user_id = cache_get(_refresh_session_lookup_key(session_key))
        if user_id is None:
            raise AppException(AppExceptionCode.INVALID_TOKEN)

        session = cache_get(_refresh_session_key(user_id, session_key))
        if session is None:
            self._delete_user_refresh_sessions(user_id)
            raise AppException(AppExceptionCode.INVALID_TOKEN)

        if session.get("user_id") != user_id or session.get("revoked") is True:
            self._delete_user_refresh_sessions(user_id)
            raise AppException(AppExceptionCode.INVALID_TOKEN)

        refresh_token = session.get("refresh_token")
        if not refresh_token:
            self._delete_user_refresh_sessions(user_id)
            raise AppException(AppExceptionCode.INVALID_TOKEN)

        payload = decode_refresh_token(refresh_token)
        if payload.get("sub") != user_id or payload.get("jti") != session_key:
            self._delete_user_refresh_sessions(user_id)
            raise AppException(AppExceptionCode.INVALID_TOKEN)

        return user_id, session_key, payload

    def _check_locked(self, email: str) -> None:
        count = redis_get_int(_lock_key(email))
        if count is not None and count >= MAX_LOGIN_ATTEMPTS:
            ttl = redis_ttl(_lock_key(email))
            remaining = math.ceil(ttl / 60)
            raise AppException(
                AppExceptionCode.ACCOUNT_LOCKED,
                f"로그인 5회 실패로 계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요.",
            )

    def _record_failure(self, email: str) -> bool:
        count = redis_incr(_lock_key(email))
        if count == 1:
            redis_expire(_lock_key(email), ATTEMPT_WINDOW_SECONDS)

        if count >= MAX_LOGIN_ATTEMPTS:
            redis_expire(_lock_key(email), LOCKOUT_SECONDS)
            return True

        return False

    def _reject_invalid_credentials(self, email: str) -> None:
        locked = self._record_failure(email)
        if locked:
            ttl = redis_ttl(_lock_key(email))
            remaining = math.ceil(ttl / 60)
            raise AppException(
                AppExceptionCode.ACCOUNT_LOCKED,
                f"로그인 5회 실패로 계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요.",
            )
        raise AppException(AppExceptionCode.INVALID_CREDENTIALS)

    def login(
        self, data: LoginRequest, request: Request, response: Response
    ) -> AccessTokenResponse:
        self._check_locked(data.email)

        user = self.repo.get_by_email(data.email)
        if not user or not user.password:
            self._reject_invalid_credentials(data.email)

        if not verify_password(data.password, user.password):
            self._reject_invalid_credentials(data.email)

        if not user.is_active:
            raise AppException(AppExceptionCode.INACTIVE_USER)

        cache_delete(_lock_key(data.email))
        try:
            self.repo.update_last_login(user)
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        session_key = self._store_refresh_session(refresh_token, request)

        response.set_cookie(
            key=REFRESH_SESSION_COOKIE,
            value=session_key,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
        )

        return AccessTokenResponse(access_token=access_token)

    def refresh(
        self, session_key: str | None, request: Request, response: Response
    ) -> AccessTokenResponse:
        user_id, jti, _ = self._get_refresh_session(session_key)

        try:
            parsed_user_id = uuid.UUID(user_id)
        except ValueError as exc:
            self._delete_user_refresh_sessions(user_id)
            raise AppException(AppExceptionCode.INVALID_TOKEN) from exc

        user = self.repo.get_by_id(parsed_user_id)

        if user is None or not user.is_active:
            raise AppException(AppExceptionCode.UNAUTHORIZED_ACCESS)

        try:
            self.repo.update_last_login(user)
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise
        self._delete_refresh_session(user_id, jti)
        new_access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)
        new_session_key = self._store_refresh_session(new_refresh_token, request)

        response.set_cookie(
            key=REFRESH_SESSION_COOKIE,
            value=new_session_key,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
        )

        return AccessTokenResponse(access_token=new_access_token)

    def logout(self, response: Response, session_key: str | None = None) -> None:
        if session_key:
            try:
                user_id = cache_get(_refresh_session_lookup_key(session_key))
                if user_id:
                    self._delete_refresh_session(user_id, session_key)
            except AppException:
                pass
        response.delete_cookie(key=REFRESH_SESSION_COOKIE)
