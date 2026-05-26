import uuid
from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.database.repository import BaseRepository
from app.domains.user.models.user import User
from app.domains.user.schemas.request import UserSearchParams


def _apply_filters(stmt: Select[tuple[User]], params: UserSearchParams) -> Select[tuple[User]]:
    if params.email is not None:
        stmt = stmt.where(User.email.ilike(f"%{params.email}%"))

    if params.name is not None:
        stmt = stmt.where(User.name.ilike(f"%{params.name}%"))

    if params.is_active is not None:
        stmt = stmt.where(User.is_active == params.is_active)

    return stmt


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        self.db.flush()

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalars(stmt).first()

    def email_exists(self, email: str) -> bool:
        stmt = select(func.count()).select_from(User).where(User.email == email)
        return (self.db.scalar(stmt) or 0) > 0

    def get_by_company(self, company_id: uuid.UUID) -> list[User]:
        stmt = select(User).where(User.company_id == company_id)
        return list(self.db.scalars(stmt).all())

    def search(self, params: UserSearchParams) -> tuple[list[User], int]:
        stmt = _apply_filters(select(User), params)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0
        users = list(self.db.scalars(stmt.offset(params.offset).limit(params.limit)).all())
        return users, total
