"""PrimeERP modular add-on engine."""

from .manifest import ModuleManifest
from .registry import ModuleRegistry, get_module_registry

__all__ = ["ModuleManifest", "ModuleRegistry", "get_module_registry"]
