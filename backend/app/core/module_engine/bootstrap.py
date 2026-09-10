"""Application bootstrap for PrimeERP add-on discovery and validation."""

from __future__ import annotations

from typing import Sequence

from .architecture import validate_catalog_dependencies, validate_manifests
from .discovery import discover_manifests
from .registry import ModuleRegistry, get_module_registry

DEFAULT_MODULE_PACKAGES: tuple[str, ...] = (
    "app.modules.accounting",
    "app.modules.sales",
    "app.modules.inventory",
    "app.modules.companies",
    "app.modules.branches",
    "app.modules.crm",
    "app.modules.hr",
    "app.modules.identity",
    "app.modules.platform",
)


def bootstrap_module_registry(
    package_names: Sequence[str] = DEFAULT_MODULE_PACKAGES,
    registry: ModuleRegistry | None = None,
) -> ModuleRegistry:
    """Discover and register all available add-ons without enabling them."""
    validate_catalog_dependencies()
    manifests = discover_manifests(package_names)
    validate_manifests(manifests)
    target = registry or get_module_registry()
    target.register_many(manifests)
    return target
