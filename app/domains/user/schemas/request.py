from pydantic import BaseModel, EmailStr, Field

from app.common.pagination import PaginationParams


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class UserSearchParams(PaginationParams):
    email: str | None = Field(default=None, description="이메일 (부분 검색)")
    name: str | None = Field(default=None, description="이름 (부분 검색)")
    is_active: bool | None = Field(default=None, description="활성화 여부")
