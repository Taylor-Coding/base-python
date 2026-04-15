import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    is_first_login: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
