from __future__ import annotations
from .commerce_adapter import CommerceAdapter

class CommerceAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, CommerceAdapter] = {}

    def register(self, adapter: CommerceAdapter) -> None:
        self._adapters[adapter.provider] = adapter

    def get(self, provider: str) -> CommerceAdapter:
        key = str(provider or "").strip().lower()
        try:
            return self._adapters[key]
        except KeyError as exc:
            raise ValueError(f"No commerce adapter registered for provider '{key}'") from exc

    def providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))

registry = CommerceAdapterRegistry()

# Built-in adapters are registered here; third-party adapters can register
# themselves at application startup without changing the core orchestrator.
from .salla_commerce_adapter import SallaCommerceAdapter
registry.register(SallaCommerceAdapter())
