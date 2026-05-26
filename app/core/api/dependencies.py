import uuid
from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.api.exceptions import AppException, AppExceptionCode
from app.core.constants.enums import UserRole
from app.core.database.session import SessionLocal
from app.core.security.crypto import decode_access_token
from app.domains.user.models.user import User
from app.domains.user.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise AppException(AppExceptionCode.MISSING_TOKEN)

    payload = decode_access_token(credentials.credentials)

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise AppException(AppExceptionCode.INVALID_TOKEN)

    try:
        parsed_user_id = uuid.UUID(user_id)
    except ValueError as exc:
        raise AppException(AppExceptionCode.INVALID_TOKEN) from exc

    repo = UserRepository(db)
    user = repo.get_by_id(parsed_user_id)
    if user is None:
        raise AppException(AppExceptionCode.NOT_FOUND_USER)

    return user


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AppException(AppExceptionCode.FORBIDDEN_ROLE)
        return current_user

    return dependency
