from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class QueryResponse(Generic[T]):
    """
    Standard repository response.
    """

    items: list[T]

    total_items: int

    page: int

    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0

        return ceil(
            self.total_items / self.page_size
        )

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1