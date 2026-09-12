"""Stable contracts for cross-module integration.

Modules should depend on these contracts rather than importing another
module's ORM models, routers, or services directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .context import ModuleContext


@dataclass(frozen=True, slots=True)
class ModuleEvent:
    name: str
    context: ModuleContext
    payload: Mapping[str, Any]
    source_module: str = "legacy"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("event name cannot be empty")
        if not self.source_module.strip():
            raise ValueError("source_module cannot be empty")


class ModuleContractError(ValueError):
    """Raised when a cross-module contract is invalid."""
