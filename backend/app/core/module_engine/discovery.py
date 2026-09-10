"""Filesystem discovery for PrimeERP add-on manifests."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterable, List

from .manifest import ModuleManifest


def discover_manifests(package_names: Iterable[str]) -> List[ModuleManifest]:
    """Discover ``__manifest__.py`` contracts below the supplied packages.

    Discovery is deliberately metadata-only. It does not import models, routers,
    or database code, keeping startup deterministic and safe for disabled add-ons.
    """
    manifests: List[ModuleManifest] = []
    for package_name in package_names:
        package = importlib.import_module(package_name)
        if not hasattr(package, "__path__"):
            continue
        for module_info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            if module_info.name.endswith(".__manifest__"):
                manifest_module = importlib.import_module(module_info.name)
                value = getattr(manifest_module, "MANIFEST", None)
                if isinstance(value, ModuleManifest):
                    manifests.append(value)
    return manifests
