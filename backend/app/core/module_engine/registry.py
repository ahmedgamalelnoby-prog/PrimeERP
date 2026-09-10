"""In-process registry and dependency validation for PrimeERP add-ons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set

from .manifest import ModuleManifest


class ModuleRegistryError(ValueError):
    """Raised when the module graph is invalid."""


@dataclass(frozen=True, slots=True)
class ModuleState:
    manifest: ModuleManifest
    installed: bool = False
    enabled: bool = False


class ModuleRegistry:
    """Central registry used by discovery and future SaaS entitlements."""

    def __init__(self) -> None:
        self._modules: Dict[str, ModuleState] = {}

    def register(self, module: ModuleManifest) -> None:
        existing = self._modules.get(module.key)
        if existing and existing.manifest.version != module.version:
            raise ModuleRegistryError(
                f"Module {module.key!r} is already registered with version {existing.manifest.version}"
            )
        self._modules[module.key] = ModuleState(
            module,
            existing.installed if existing else False,
            existing.enabled if existing else False,
        )

    def register_many(self, modules: Iterable[ModuleManifest]) -> None:
        """Register as a batch so dependency order does not matter."""
        for module in modules:
            self.register(module)
        self.validate_graph()

    def get(self, technical_name: str) -> ModuleManifest:
        try:
            return self._modules[technical_name].manifest
        except KeyError as exc:
            raise ModuleRegistryError(f"Unknown module: {technical_name}") from exc

    def all(self) -> List[ModuleManifest]:
        return [state.manifest for state in self._modules.values()]

    def state(self, technical_name: str) -> ModuleState:
        try:
            return self._modules[technical_name]
        except KeyError as exc:
            raise ModuleRegistryError(f"Unknown module: {technical_name}") from exc

    def enable(self, technical_name: str) -> None:
        module = self.get(technical_name)
        if not module.installable:
            raise ModuleRegistryError(f"Module {technical_name} is not installable")
        for dependency in module.dependencies:
            dependency_state = self._modules.get(dependency)
            if not dependency_state or not dependency_state.enabled:
                raise ModuleRegistryError(
                    f"Cannot enable {technical_name}: dependency {dependency} is not enabled"
                )
        self._modules[technical_name] = ModuleState(module, installed=True, enabled=True)

    def disable(self, technical_name: str) -> None:
        self.state(technical_name)
        dependents = [
            name
            for name, state in self._modules.items()
            if state.enabled and technical_name in state.manifest.dependencies
        ]
        if dependents:
            raise ModuleRegistryError(
                f"Cannot disable {technical_name}: enabled dependents exist: {', '.join(dependents)}"
            )
        module = self.get(technical_name)
        self._modules[technical_name] = ModuleState(module, installed=True, enabled=False)

    def validate_graph(self) -> None:
        for module in self._modules.values():
            self._validate_dependency_names(module.manifest)
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(name: str) -> None:
            if name in visiting:
                raise ModuleRegistryError(f"Circular module dependency detected at {name}")
            if name in visited:
                return
            visiting.add(name)
            for dependency in self.get(name).dependencies:
                visit(dependency)
            visiting.remove(name)
            visited.add(name)

        for name in self._modules:
            visit(name)

    def _validate_dependency_names(self, module: ModuleManifest) -> None:
        missing = [name for name in module.dependencies if name not in self._modules]
        if missing:
            raise ModuleRegistryError(
                f"Module {module.key} has missing dependencies: {', '.join(missing)}"
            )


_registry = ModuleRegistry()


def get_module_registry() -> ModuleRegistry:
    """Return the process-wide registry instance."""
    return _registry
