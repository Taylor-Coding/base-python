import uuid

from fastapi import APIRouter, Depends

from app.core.api.dependencies import get_current_user, require_roles
from app.core.api.pagination import PageResult
from app.core.constants.enums import UserRole
from app.domains.user.models.user import User
from app.domains.user.routers.dependencies import get_user_service
from app.domains.user.schemas.request import UserSearchParams, UserUpdate
from app.domains.user.schemas.response import UserResponse
from app.domains.user.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=PageResult[UserResponse],
    dependencies=[Depends(require_roles(UserRole.MASTER, UserRole.ADMIN))],
)
def search_users(
    params: UserSearchParams = Depends(),
    service: UserService = Depends(get_user_service),
):
    return service.search_users(params)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return service.get_user_for(user_id, current_user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return service.update_user_for(user_id, data, current_user)


@router.delete(
    "/{user_id}",
    status_code=204,
    dependencies=[Depends(require_roles(UserRole.MASTER, UserRole.ADMIN))],
)
def delete_user(user_id: uuid.UUID, service: UserService = Depends(get_user_service)):
    service.delete_user(user_id)
