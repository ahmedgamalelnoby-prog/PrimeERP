"""PrimeERP modular add-on engine."""

from .bus import ModuleEventBus, get_module_event_bus
from .context import ModuleContext
from .contracts import ModuleContractError, ModuleEvent
from .entitlement import ModuleEntitlement, ModuleEntitlementStore
from .manifest import ModuleManifest
from .permissions import ModulePermissionService
from .registry import ModuleRegistry, ModuleRegistryError, ModuleState, get_module_registry

__all__ = [
    "ModuleContext",
    "ModuleContractError",
    "ModuleEntitlement",
    "ModuleEntitlementStore",
    "ModuleEvent",
    "ModuleEventBus",
    "ModuleManifest",
    "ModulePermissionService",
    "ModuleRegistry",
    "ModuleRegistryError",
    "ModuleState",
    "get_module_event_bus",
    "get_module_registry",
]
