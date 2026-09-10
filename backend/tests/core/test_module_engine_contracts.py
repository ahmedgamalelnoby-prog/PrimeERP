from datetime import datetime, timedelta, timezone

import pytest

from app.core.module_engine import (
    ModuleContext,
    ModuleEntitlement,
    ModuleEntitlementStore,
    ModuleEvent,
    ModuleEventBus,
    ModuleManifest,
    ModulePermissionService,
    ModuleRegistry,
    ModuleRegistryError,
)


def test_context_requires_tenant() -> None:
    context = ModuleContext(tenant_id=" tenant-1 ", user_id="user-1")
    assert context.require_tenant() == " tenant-1 "
    with pytest.raises(ValueError):
        ModuleContext(tenant_id="").require_tenant()


def test_registry_install_and_version_state() -> None:
    registry = ModuleRegistry()
    registry.register(ModuleManifest("accounting/core", "Accounting Core", version="2.0.0"))
    registry.install("accounting/core")
    state = registry.state("accounting/core")
    assert state.installed is True
    assert state.enabled is False
    assert state.installed_version == "2.0.0"


def test_tenant_entitlement_expires() -> None:
    store = ModuleEntitlementStore()
    store.grant(
        ModuleEntitlement(
            "sales/core",
            "tenant-1",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
    )
    assert store.is_enabled("tenant-1", "sales/core") is True
    assert store.is_enabled("tenant-2", "sales/core") is False


def test_permission_service_uses_manifest_contract() -> None:
    registry = ModuleRegistry()
    registry.register(
        ModuleManifest(
            "sales/orders",
            "Sales Orders",
            permissions=frozenset({"sales.orders.read", "sales.orders.write"}),
        )
    )
    service = ModulePermissionService(registry)
    assert service.is_declared("sales/orders", "sales.orders.read") is True
    assert service.is_declared("sales/orders", "sales.orders.delete") is False
    with pytest.raises(ModuleRegistryError):
        service.require_declared("sales/orders", "sales.orders.delete")


def test_event_bus_dispatches_without_module_imports() -> None:
    bus = ModuleEventBus()
    received = []
    bus.subscribe("sales.order.created", received.append)
    event = ModuleEvent(
        name="sales.order.created",
        context=ModuleContext("tenant-1", "user-1"),
        payload={"order_id": "SO-1"},
        source_module="sales/orders",
    )
    bus.publish(event)
    assert received == [event]
