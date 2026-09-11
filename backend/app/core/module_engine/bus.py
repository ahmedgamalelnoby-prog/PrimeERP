"""Small synchronous event bus for module integration boundaries."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, DefaultDict, List

from .contracts import ModuleEvent


ModuleHandler = Callable[[ModuleEvent], None]


class ModuleEventBus:
    """In-process bus; transport can later be replaced without changing contracts."""

    def __init__(self) -> None:
        self._handlers: DefaultDict[str, List[ModuleHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: ModuleHandler) -> None:
        if not event_name.strip():
            raise ValueError("event_name cannot be empty")
        if handler not in self._handlers[event_name]:
            self._handlers[event_name].append(handler)

    def publish(self, event: ModuleEvent) -> None:
        for handler in tuple(self._handlers.get(event.name, ())):
            handler(event)

    def clear(self, event_name: str | None = None) -> None:
        if event_name is None:
            self._handlers.clear()
        else:
            self._handlers.pop(event_name, None)


_event_bus = ModuleEventBus()


def get_module_event_bus() -> ModuleEventBus:
    return _event_bus
