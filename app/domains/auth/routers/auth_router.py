from fastapi import APIRouter, Cookie, Depends, Request, Response, status

from app.domains.auth.routers.dependencies import get_auth_service, get_user_service
from app.domains.auth.schemas.request import LoginRequest
from app.domains.auth.schemas.response import AccessTokenResponse
from app.domains.auth.services.auth_service import REFRESH_SESSION_COOKIE, AuthService
from app.domains.user.schemas.request import UserCreate
from app.domains.user.schemas.response import UserResponse
from app.domains.user.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.register(data)


@router.post("/login", response_model=AccessTokenResponse)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    return service.login(data, request, response)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(
    request: Request,
    response: Response,
    session_key: str | None = Cookie(default=None, alias=REFRESH_SESSION_COOKIE),
    service: AuthService = Depends(get_auth_service),
):
    return service.refresh(session_key, request, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session_key: str | None = Cookie(default=None, alias=REFRESH_SESSION_COOKIE),
    service: AuthService = Depends(get_auth_service),
):
    service.logout(response, session_key)
