from __future__ import annotations

from math import ceil
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, Field


ItemType = TypeVar("ItemType")


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool


class PaginatedResponse(
    BaseModel,
    Generic[ItemType],
):
    items: list[ItemType]
    meta: PaginationMeta


def calculate_pages(
    total: int,
    page_size: int,
) -> int:
    if total <= 0:
        return 0

    return ceil(total / page_size)


def build_paginated_response(
    *,
    items: Sequence[ItemType],
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse[ItemType]:
    pages = calculate_pages(
        total,
        page_size,
    )

    return PaginatedResponse(
        items=list(items),
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_previous=page > 1,
        ),
    )