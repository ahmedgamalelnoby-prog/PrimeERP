"""Provider-neutral adapter boundary for commerce integrations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from .commerce_contracts import CanonicalOrder


class CommerceAdapter(ABC):
    """Translate one external commerce platform into PrimeERP's canonical model.

    The adapter owns authentication, API/webhook payloads and provider-specific
    status/field names. It must not post PrimeERP accounting entries directly.
    """

    provider: str

    @abstractmethod
    def normalize_order(self, db: Session, connection: Any, payload: dict[str, Any]) -> CanonicalOrder:
        raise NotImplementedError

    def normalize_event(self, db: Session, connection: Any, event_type: str, payload: dict[str, Any]) -> CanonicalOrder | None:
        if event_type.startswith("order"):
            return self.normalize_order(db, connection, payload)
        return None
