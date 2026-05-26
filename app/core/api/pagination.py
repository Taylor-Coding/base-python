from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="페이지 번호")
    size: int = Field(default=20, ge=1, le=100, description="페이지 당 항목 수")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class PageMeta(BaseModel):
    page_number: int
    page_size: int
    total_elements: int
    total_pages: int
    is_first: bool
    is_last: bool


class PageResult(BaseModel, Generic[T]):
    data: list[T]
    meta: PageMeta

    @classmethod
    def of(cls, data: list[T], total_elements: int, params: PaginationParams) -> "PageResult[T]":
        total_pages = (total_elements + params.size - 1) // params.size if total_elements > 0 else 0
        return cls(
            data=data,
            meta=PageMeta(
                page_number=params.page,
                page_size=params.size,
                total_elements=total_elements,
                total_pages=total_pages,
                is_first=params.page == 1,
                is_last=params.page >= total_pages,
            ),
        )
