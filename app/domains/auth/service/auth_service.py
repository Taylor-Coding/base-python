import math

from fastapi import Response

from app.core.config import settings
from app.core.exceptions import AppException, AppExceptionCode
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from app.domains.auth.schemas import AccessTokenResponse, LoginRequest
from app.domains.user.repository import UserRepository
from app.integrations.redis import cache_delete, redis_expire, redis_get_int, redis_incr, redis_ttl

REFRESH_TOKEN_COOKIE = "refresh_token"
MAX_LOGIN_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 300  # 5분: 잠금 없이 시도 횟수 유지 기간
LOCKOUT_SECONDS = 300  # 5분: 잠금 지속 시간


def _lock_key(email: str) -> str:
    return f"login_lock:{email}"


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

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

    def login(self, data: LoginRequest, response: Response) -> AccessTokenResponse:
        self._check_locked(data.email)

        user = self.repo.get_by_email(data.email)
        if not user or not user.password:
            raise AppException(AppExceptionCode.INVALID_CREDENTIALS)

        if not verify_password(data.password, user.password):
            locked = self._record_failure(data.email)
            if locked:
                ttl = redis_ttl(_lock_key(data.email))
                remaining = math.ceil(ttl / 60)
                raise AppException(
                    AppExceptionCode.ACCOUNT_LOCKED,
                    f"로그인 5회 실패로 계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요.",
                )
            raise AppException(AppExceptionCode.INVALID_CREDENTIALS)

        if not user.is_active:
            raise AppException(AppExceptionCode.INACTIVE_USER)

        cache_delete(_lock_key(data.email))
        self.repo.update_last_login(user)
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE,
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
        )

        return AccessTokenResponse(access_token=access_token)

    def refresh(self, refresh_token: str | None, response: Response) -> AccessTokenResponse:
        if not refresh_token:
            raise AppException(AppExceptionCode.MISSING_TOKEN)

        payload = decode_refresh_token(refresh_token)
        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise AppException(AppExceptionCode.INVALID_TOKEN)

        import uuid

        user = self.repo.get_by_id(uuid.UUID(user_id))

        if user is None or not user.is_active:
            raise AppException(AppExceptionCode.UNAUTHORIZED_ACCESS)

        self.repo.update_last_login(user)
        new_access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)

        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE,
            value=new_refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
        )

        return AccessTokenResponse(access_token=new_access_token)

    def logout(self, response: Response) -> None:
        response.delete_cookie(key=REFRESH_TOKEN_COOKIE)
