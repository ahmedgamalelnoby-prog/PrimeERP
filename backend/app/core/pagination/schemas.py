from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationRequest(BaseModel):
    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=25,
        ge=1,
        le=100,
    )


class PaginationMetadata(BaseModel):
    page: int

    page_size: int

    total_records: int

    total_pages: int

    has_next: bool

    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]

    pagination: PaginationMetadata