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

REFRESH_TOKEN_COOKIE = "refresh_token"


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def login(self, data: LoginRequest, response: Response) -> AccessTokenResponse:
        user = self.repo.get_by_email(data.email)
        if not user or not user.hashed_password:
            raise AppException(AppExceptionCode.INVALID_CREDENTIALS)
        if not verify_password(data.password, user.hashed_password):
            raise AppException(AppExceptionCode.INVALID_CREDENTIALS)
        if not user.is_active:
            raise AppException(AppExceptionCode.INACTIVE_USER)

        if user.is_first_login:
            user.is_first_login = False
            self.repo.update(user)

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
