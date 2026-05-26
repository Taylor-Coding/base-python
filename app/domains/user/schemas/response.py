import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.constants.enums import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    full_name: str | None
    role: UserRole
    company_id: uuid.UUID | None
    is_active: bool
    is_first_login: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
