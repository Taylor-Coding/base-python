from sqlalchemy.orm import Query, Session

from app.common.base_repository import BaseRepository
from app.domains.user.models import User
from app.domains.user.schemas import UserSearchParams


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def email_exists(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).count() > 0

    def search(self, params: UserSearchParams) -> tuple[list[User], int]:
        query = self._apply_filters(self.db.query(User), params)
        total = query.count()
        users = query.offset(params.offset).limit(params.limit).all()
        return users, total

    def _apply_filters(self, query: Query, params: UserSearchParams) -> Query:
        if params.email is not None:
            query = query.filter(User.email.ilike(f"%{params.email}%"))
        if params.full_name is not None:
            query = query.filter(User.full_name.ilike(f"%{params.full_name}%"))
        if params.is_active is not None:
            query = query.filter(User.is_active == params.is_active)
        return query
