"""Lifecycle helpers for installable PrimeERP add-ons."""

from __future__ import annotations

from .registry import ModuleRegistry


class ModuleLifecycle:
    """Application-facing facade over registry state changes."""

    def __init__(self, registry: ModuleRegistry) -> None:
        self.registry = registry

    def install_and_enable(self, technical_name: str) -> None:
        self.registry.install(technical_name)
        self.registry.enable(technical_name)

    def uninstall(self, technical_name: str) -> None:
        # Financial/data destruction is intentionally not implemented here.
        # Future uninstall handlers must provide safe migrations/retention rules.
        self.registry.disable(technical_name)
