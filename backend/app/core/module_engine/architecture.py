"""Architecture validation for the PrimeERP modular monolith.

This layer enforces boundaries without coupling add-ons to one another's ORM
internals. It is intentionally small enough to run during CI and application
startup checks.
"""

from __future__ import annotations

from typing import Iterable

from .catalog import catalog_keys
from .manifest import ModuleManifest


class ModuleArchitectureError(ValueError):
    """Raised when an add-on violates the canonical architecture contract."""


def validate_manifests(manifests: Iterable[ModuleManifest]) -> None:
    """Validate names, uniqueness, and dependency references for manifests."""
    items = list(manifests)
    seen: dict[str, ModuleManifest] = {}
    for module in items:
        if module.key in seen and seen[module.key].version != module.version:
            raise ModuleArchitectureError(
                f"Conflicting versions registered for {module.key}: "
                f"{seen[module.key].version} and {module.version}"
            )
        seen[module.key] = module

    for module in seen.values():
        for dependency in module.dependencies:
            if dependency not in seen:
                raise ModuleArchitectureError(
                    f"{module.key} depends on unregistered module {dependency}"
                )

    known = catalog_keys()
    unknown = sorted(key for key in seen if key not in known)
    if unknown:
        raise ModuleArchitectureError(
            "Manifest(s) are missing from the canonical module catalog: "
            + ", ".join(unknown)
        )


def validate_catalog_dependencies() -> None:
    """Validate the catalog itself without requiring business modules to load."""
    from .catalog import catalog

    entries = {entry.technical_name: entry for entry in catalog()}
    for entry in entries.values():
        for dependency in entry.dependencies:
            if dependency not in entries:
                raise ModuleArchitectureError(
                    f"Catalog entry {entry.technical_name} references unknown {dependency}"
                )

        if entry.technical_name in entry.dependencies:
            raise ModuleArchitectureError(
                f"Catalog entry {entry.technical_name} depends on itself"
            )
