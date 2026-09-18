from __future__ import annotations

from .commerce_adapter import CommerceAdapter


class CommerceAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, CommerceAdapter] = {}

    def register(self, adapter: CommerceAdapter) -> None:
        self._adapters[adapter.provider] = adapter

    def get(self, provider: str) -> CommerceAdapter:
        try:
            return self._adapters[provider]
        except KeyError as exc:
            raise ValueError(f"No commerce adapter registered for provider '{provider}'") from exc


registry = CommerceAdapterRegistry()
