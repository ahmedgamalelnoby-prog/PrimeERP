"""PrimeERP modular add-on engine."""

from .entitlement import ModuleEntitlement, ModuleEntitlementStore
from .manifest import ModuleManifest
from .permissions import ModulePermissionService
from .registry import ModuleRegistry, ModuleRegistryError, ModuleState, get_module_registry

__all__ = [
    "ModuleEntitlement",
    "ModuleEntitlementStore",
    "ModuleManifest",
    "ModulePermissionService",
    "ModuleRegistry",
    "ModuleRegistryError",
    "ModuleState",
    "get_module_registry",
]
