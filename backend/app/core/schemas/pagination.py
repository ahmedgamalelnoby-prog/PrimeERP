from __future__ import annotations

from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class PageMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)

    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta

    @classmethod
    def create(
        cls,
        *,
        items: list[T],
        page: int,
        page_size: int,
        total: int,
    ) -> "PaginatedResponse[T]":
        safe_page = max(page, 1)
        safe_page_size = max(page_size, 1)
        safe_total = max(total, 0)

        total_pages = (
            ceil(safe_total / safe_page_size)
            if safe_total > 0
            else 0
        )

        return cls(
            items=items,
            meta=PageMeta(
                page=safe_page,
                page_size=safe_page_size,
                total=safe_total,
                total_pages=total_pages,
                has_next=(
                    safe_page < total_pages
                ),
                has_previous=(
                    safe_page > 1
                    and total_pages > 0
                ),
            ),
        )