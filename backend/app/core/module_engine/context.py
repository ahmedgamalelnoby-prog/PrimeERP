"""Request context shared across modular ERP contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class ModuleContext:
    """Minimal context a module may receive from the platform.

    Modules must use this context instead of reaching into another module's
    internal authentication, tenant, or request state.
    """

    tenant_id: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None

    def require_tenant(self) -> str:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        return self.tenant_id
