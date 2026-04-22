from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.domains.user.models import Organization


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_name(self, name: str) -> Organization | None:
        stmt = select(Organization).where(Organization.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def name_exists(self, name: str) -> bool:
        stmt = select(Organization).where(Organization.name == name)
        return self.db.execute(stmt).first() is not None
