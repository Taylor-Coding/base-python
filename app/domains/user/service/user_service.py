import uuid

from app.common.pagination import PageResult
from app.core.exceptions import AppException, AppExceptionCode
from app.core.security import hash_password
from app.domains.user.models import User
from app.domains.user.repository import UserRepository
from app.domains.user.schemas import UserCreate, UserSearchParams, UserUpdate


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def register(self, data: UserCreate) -> User:
        if self.repo.email_exists(data.email):
            raise AppException(AppExceptionCode.DUPLICATE_EMAIL)
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        return self.repo.create(user)

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise AppException(AppExceptionCode.NOT_FOUND_USER)
        return user

    def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        user = self.get_user(user_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        return self.repo.update(user)

    def delete_user(self, user_id: uuid.UUID) -> None:
        user = self.get_user(user_id)
        self.repo.delete(user)

    def search_users(self, params: UserSearchParams) -> PageResult:
        users, total = self.repo.search(params)
        return PageResult.of(users, total, params)
