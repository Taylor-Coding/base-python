import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Query, Session

from app.common.base_repository import BaseRepository
from app.domains.user.models import User
from app.domains.user.schemas import UserSearchParams


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        self.db.flush()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def email_exists(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).count() > 0

    def get_by_organization(self, organization_id: uuid.UUID) -> list[User]:
        return self.db.query(User).filter(User.organization_id == organization_id).all()

    def search(self, params: UserSearchParams) -> tuple[list[User], int]:
        query = self._apply_filters(self.db.query(User), params)
        total = query.count()
        users = query.offset(params.offset).limit(params.limit).all()
        return users, total

    def _apply_filters(self, query: Query, params: UserSearchParams) -> Query:
        if params.email is not None:
            query = query.filter(User.email.ilike(f"%{params.email}%"))
        if params.name is not None:
            query = query.filter(User.name.ilike(f"%{params.name}%"))
        if params.is_active is not None:
            query = query.filter(User.is_active == params.is_active)
        return query
