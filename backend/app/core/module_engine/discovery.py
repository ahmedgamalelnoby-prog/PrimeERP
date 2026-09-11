"""Filesystem discovery and registration for PrimeERP add-on manifests."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable, List

from .manifest import ModuleManifest
from .registry import ModuleRegistry, ModuleRegistryError


def discover_manifests(package_names: Iterable[str]) -> List[ModuleManifest]:
    """Discover metadata-only manifests below the supplied packages.

    Results are deterministic and deduplicated by technical module name. A
    duplicate name is accepted only when it exposes the exact same version.
    Business modules are never imported as part of discovery.
    """
    discovered: dict[str, ModuleManifest] = {}
    for package_name in package_names:
        package = importlib.import_module(package_name)
        if not hasattr(package, "__path__"):
            continue
        for module_info in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            if not module_info.name.endswith(".__manifest__"):
                continue
            manifest_module = importlib.import_module(module_info.name)
            value = getattr(manifest_module, "MANIFEST", None)
            if not isinstance(value, ModuleManifest):
                continue
            existing = discovered.get(value.key)
            if existing is not None and existing.version != value.version:
                raise ModuleRegistryError(
                    f"Conflicting manifest versions for {value.key!r}: "
                    f"{existing.version} and {value.version}"
                )
            discovered[value.key] = value
    return [discovered[key] for key in sorted(discovered)]


def register_discovered(
    registry: ModuleRegistry, package_names: Iterable[str]
) -> List[ModuleManifest]:
    """Discover and register all valid add-ons into a registry."""
    manifests = discover_manifests(package_names)
    registry.register_many(manifests)
    return manifests
