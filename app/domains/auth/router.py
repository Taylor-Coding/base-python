from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.domains.auth.schemas import AccessTokenResponse, LoginRequest
from app.domains.auth.service import AuthService
from app.domains.user.repository import UserRepository
from app.domains.user.schemas import UserCreate, UserResponse
from app.domains.user.service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.register(data)


@router.post("/login", response_model=AccessTokenResponse)
def login(
    data: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    return service.login(data, response)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    service: AuthService = Depends(get_auth_service),
):
    return service.refresh(refresh_token, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    service.logout(response)
