"""Application bootstrap for PrimeERP add-on discovery and validation."""

from __future__ import annotations

import importlib
from typing import Sequence

from .architecture import validate_catalog_dependencies, validate_manifests
from .discovery import discover_manifests
from .registry import ModuleRegistry, get_module_registry

DEFAULT_MODULE_PACKAGE = "app.modules"


def bootstrap_module_registry(
    package_names: Sequence[str] | None = None,
    registry: ModuleRegistry | None = None,
) -> ModuleRegistry:
    """Discover, register, and validate every available add-on."""
    validate_catalog_dependencies()
    packages = tuple(package_names) if package_names is not None else (DEFAULT_MODULE_PACKAGE,)
    for package_name in packages:
        importlib.import_module(package_name)
    manifests = discover_manifests(packages)
    validate_manifests(manifests)
    target = registry or get_module_registry()
    target.register_many(manifests)
    target.validate_graph()
    return target
