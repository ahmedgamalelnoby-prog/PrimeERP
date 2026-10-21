"""Permission registration and checks for modular add-ons."""

from __future__ import annotations

from typing import Iterable, Set

from .manifest import ModuleManifest
from .registry import ModuleRegistry, ModuleRegistryError


class ModulePermissionService:
    """Validates permissions declared by manifests without owning user roles."""

    def __init__(self, registry: ModuleRegistry) -> None:
        self.registry = registry

    def permissions_for(self, technical_name: str) -> Set[str]:
        return set(self.registry.get(technical_name).permissions)

    def is_declared(self, technical_name: str, permission: str) -> bool:
        return permission in self.registry.get(technical_name).permissions

    def require_declared(self, technical_name: str, permission: str) -> None:
        if not self.is_declared(technical_name, permission):
            raise ModuleRegistryError(
                f"Permission {permission!r} is not declared by module {technical_name}"
            )

    @staticmethod
    def normalize(permissions: Iterable[str]) -> Set[str]:
        return {permission.strip() for permission in permissions if permission.strip()}
