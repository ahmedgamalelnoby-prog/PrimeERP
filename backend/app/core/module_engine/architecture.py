"""Architecture validation for the PrimeERP modular monolith."""

from __future__ import annotations

from typing import Iterable

from .catalog import catalog, catalog_keys
from .manifest import ModuleManifest


class ModuleArchitectureError(ValueError):
    """Raised when an add-on violates the modular architecture contract."""


def validate_manifests(
    manifests: Iterable[ModuleManifest], *, strict_catalog: bool = False
) -> None:
    """Validate manifest uniqueness and dependency references.

    ``strict_catalog`` is opt-in during the migration period because legacy
    compatibility add-ons may exist before their canonical catalog entry is
    promoted. Production bootstrap validates the graph immediately while the
    catalog can be expanded incrementally without blocking existing modules.
    """
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

    if strict_catalog:
        unknown = sorted(key for key in seen if key not in catalog_keys())
        if unknown:
            raise ModuleArchitectureError(
                "Manifest(s) are missing from the canonical module catalog: "
                + ", ".join(unknown)
            )


def validate_catalog_dependencies() -> None:
    """Validate the canonical catalog itself, including cycles."""
    entries = {entry.technical_name: entry for entry in catalog()}
    for entry in entries.values():
        for dependency in entry.dependencies:
            if dependency not in entries:
                raise ModuleArchitectureError(
                    f"Catalog entry {entry.technical_name} references unknown {dependency}"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise ModuleArchitectureError(f"Circular catalog dependency at {name}")
        if name in visited:
            return
        visiting.add(name)
        for dependency in entries[name].dependencies:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)

    for name in entries:
        visit(name)
