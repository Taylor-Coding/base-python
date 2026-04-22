import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_roles
from app.domains.user.enums import UserRole
from app.domains.user.models import User
from app.domains.user.repository import UserRepository
from app.common.pagination import PageResult
from app.domains.user.schemas import (
    UserResponse,
    UserSearchParams,
    UserUpdate,
)
from app.domains.user.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("", response_model=PageResult[UserResponse], dependencies=[Depends(require_roles(UserRole.MASTER, UserRole.ADMIN))])
def search_users(params: UserSearchParams = Depends(), service: UserService = Depends(get_service)):
    return service.search_users(params)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, service: UserService = Depends(get_service)):
    return service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: uuid.UUID, data: UserUpdate, service: UserService = Depends(get_service)):
    return service.update_user(user_id, data)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: uuid.UUID, service: UserService = Depends(get_service)):
    service.delete_user(user_id)
