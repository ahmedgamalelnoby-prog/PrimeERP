from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class QueryOptions:
    """
    Defines the fields permitted for filtering, searching and sorting.

    Repositories can override these options for each model.
    """

    filterable_fields: set[str] = field(default_factory=set)
    searchable_fields: set[str] = field(default_factory=set)
    sortable_fields: set[str] = field(default_factory=set)