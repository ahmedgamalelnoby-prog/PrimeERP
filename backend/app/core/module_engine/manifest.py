"""Manifest contract for PrimeERP add-ons.

A manifest is the stable metadata contract between an add-on and the platform.
Business logic must stay inside the add-on; the platform only consumes metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Mapping, Tuple


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    """Immutable metadata describing one installable ERP add-on."""

    technical_name: str
    display_name: str
    version: str = "1.0.0"
    domain: str = "core"
    dependencies: Tuple[str, ...] = ()
    optional_dependencies: Tuple[str, ...] = ()
    permissions: FrozenSet[str] = frozenset()
    routes: Tuple[str, ...] = ()
    menus: Tuple[str, ...] = ()
    installable: bool = True
    tenant_enabled: bool = True
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.technical_name or "/" not in self.technical_name:
            raise ValueError("technical_name must use the '<domain>/<addon>' format")
        if not self.display_name.strip():
            raise ValueError("display_name cannot be empty")
        if self.technical_name in self.dependencies:
            raise ValueError("a module cannot depend on itself")

    @property
    def key(self) -> str:
        return self.technical_name


def manifest(**kwargs: object) -> ModuleManifest:
    """Small helper for add-on ``__manifest__.py`` files."""
    return ModuleManifest(**kwargs)  # type: ignore[arg-type]
