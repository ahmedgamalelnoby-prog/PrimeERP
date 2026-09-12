"""Tenant-level module entitlements.

Platform installation and tenant entitlement are intentionally separate concerns.
This in-memory contract is the foundation for persistent SaaS subscription data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass(frozen=True, slots=True)
class ModuleEntitlement:
    """Tenant entitlement for a technical module.

    The positional contract is ``technical_name, tenant_id``. Keyword
    construction is recommended for new code to make the two identifiers explicit.
    """

    technical_name: str
    tenant_id: str
    enabled: bool = True
    expires_at: Optional[datetime] = None
    plan_code: Optional[str] = None
    source: Optional[str] = None

    def is_active(self, now: Optional[datetime] = None) -> bool:
        if not self.enabled:
            return False
        if self.expires_at is None:
            return True
        current = now or datetime.now(timezone.utc)
        expiry = self.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry > current


class ModuleEntitlementStore:
    """Process-local store used until SaaS entitlement persistence is introduced."""

    def __init__(self) -> None:
        self._items: Dict[tuple[str, str], ModuleEntitlement] = {}

    def grant(self, entitlement: ModuleEntitlement) -> None:
        self._items[(entitlement.tenant_id, entitlement.technical_name)] = entitlement

    def revoke(self, tenant_id: str, technical_name: str) -> None:
        current = self._items.get((tenant_id, technical_name))
        if current is not None:
            self._items[(tenant_id, technical_name)] = ModuleEntitlement(
                technical_name=current.technical_name,
                tenant_id=current.tenant_id,
                enabled=False,
                expires_at=current.expires_at,
                plan_code=current.plan_code,
                source=current.source,
            )

    def get(self, tenant_id: str, technical_name: str) -> Optional[ModuleEntitlement]:
        return self._items.get((tenant_id, technical_name))

    def is_enabled(self, tenant_id: str, technical_name: str) -> bool:
        item = self.get(tenant_id, technical_name)
        return item is not None and item.is_active()
