from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


@dataclass(slots=True)
class QueryRequest:
    """
    Generic query request used by every repository.
    """

    filters: dict[str, Any] = field(default_factory=dict)

    search: str | None = None

    sort: str | None = None

    page: int = DEFAULT_PAGE

    page_size: int = DEFAULT_PAGE_SIZE

    include_deleted: bool = False