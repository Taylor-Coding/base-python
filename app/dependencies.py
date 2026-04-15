import uuid
from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, AppExceptionCode
from app.core.security import decode_access_token
from app.database import SessionLocal
from app.domains.user.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
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

    repo = UserRepository(db)
    user = repo.get_by_id(uuid.UUID(user_id))
    if user is None:
        raise AppException(AppExceptionCode.NOT_FOUND_USER)

    return user
