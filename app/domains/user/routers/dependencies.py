from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.api.dependencies import get_db
from app.domains.user.repositories.user_repository import UserRepository
from app.domains.user.services.user_service import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))
