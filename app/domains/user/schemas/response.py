import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domains.user.enums import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    role: UserRole
    organization_id: uuid.UUID | None
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
