import uuid

from sqlalchemy.exc import IntegrityError

from app.core.api.exceptions import AppException, AppExceptionCode
from app.core.api.pagination import PageResult
from app.core.constants.enums import UserRole
from app.core.security.crypto import hash_password
from app.domains.user.models.user import User
from app.domains.user.repositories.user_repository import UserRepository
from app.domains.user.schemas.request import UserCreate, UserSearchParams, UserUpdate


class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def _is_admin(self, user: User) -> bool:
        return user.role in {UserRole.MASTER, UserRole.ADMIN}

    def _ensure_self_or_admin(self, current_user: User, target_user_id: uuid.UUID) -> None:
        if current_user.id == target_user_id or self._is_admin(current_user):
            return
        raise AppException(AppExceptionCode.FORBIDDEN_ROLE)

    def _ensure_self(self, current_user: User, target_user_id: uuid.UUID) -> None:
        if current_user.id == target_user_id:
            return
        raise AppException(AppExceptionCode.FORBIDDEN_ROLE)

    def _update_values_for(self, data: UserUpdate, current_user: User) -> dict:
        values = data.model_dump(exclude_none=True)
        if not self._is_admin(current_user) and "is_active" in values:
            raise AppException(AppExceptionCode.FORBIDDEN_ROLE)
        return values

    def register(self, data: UserCreate) -> User:
        if self.repo.email_exists(data.email):
            raise AppException(AppExceptionCode.DUPLICATE_EMAIL)

        user = User(
            email=data.email,
            password=hash_password(data.password),
            name=data.name,
        )

        try:
            user = self.repo.create(user)
            self.repo.commit()
            return user
        except IntegrityError as exc:
            self.repo.rollback()
            raise AppException(AppExceptionCode.DUPLICATE_EMAIL) from exc
        except Exception:
            self.repo.rollback()
            raise

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.repo.get_by_id(user_id)

        if not user:
            raise AppException(AppExceptionCode.NOT_FOUND_USER)

        return user

    def get_user_for(self, user_id: uuid.UUID, current_user: User) -> User:
        self._ensure_self_or_admin(current_user, user_id)
        return self.get_user(user_id)

    def update_user(self, user_id: uuid.UUID, values: dict) -> User:
        user = self.get_user(user_id)

        for field, value in values.items():
            setattr(user, field, value)

        try:
            user = self.repo.update(user)
            self.repo.commit()
            return user
        except Exception:
            self.repo.rollback()
            raise

    def update_user_for(self, user_id: uuid.UUID, data: UserUpdate, current_user: User) -> User:
        self._ensure_self_or_admin(current_user, user_id)
        return self.update_user(user_id, self._update_values_for(data, current_user))

    def delete_user(self, user_id: uuid.UUID) -> None:
        user = self.get_user(user_id)
        try:
            self.repo.delete(user)
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise

    def search_users(self, params: UserSearchParams) -> PageResult:
        users, total = self.repo.search(params)

        return PageResult.of(users, total, params)
