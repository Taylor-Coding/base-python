from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.domains.project.models import Project


class ProjectRepository(BaseRepository[Project]):
    model = Project

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_status(self, status: str) -> list[Project]:
        return self.db.query(Project).filter(Project.status == status).all()
