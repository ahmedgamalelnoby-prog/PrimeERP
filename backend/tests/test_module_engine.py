from datetime import datetime, timedelta, timezone
import unittest

from app.core.module_engine import (
    ModuleContext,
    ModuleEntitlement,
    ModuleEvent,
    ModuleEventBus,
    ModuleManifest,
    ModulePermissionService,
    ModuleRegistry,
    ModuleRegistryError,
)
from app.core.module_engine.discovery import discover_manifests
from app.core.module_engine.lifecycle import ModuleLifecycle


class ModuleEngineTests(unittest.TestCase):
    def manifest(self, name, dependencies=(), permissions=()):
        return ModuleManifest(
            technical_name=name,
            display_name=name,
            dependencies=tuple(dependencies),
            permissions=frozenset(permissions),
        )

    def test_dependency_graph_is_order_independent(self):
        registry = ModuleRegistry()
        child = self.manifest("sales/orders", ("sales/core",))
        core = self.manifest("sales/core")
        registry.register_many([child, core])
        registry.enable("sales/core")
        registry.enable("sales/orders")
        self.assertTrue(registry.state("sales/orders").enabled)

    def test_missing_and_circular_dependencies_are_rejected(self):
        registry = ModuleRegistry()
        with self.assertRaises(ModuleRegistryError):
            registry.register_many([self.manifest("sales/orders", ("sales/core",))])

        circular = ModuleRegistry()
        a = self.manifest("a/core", ("b/core",))
        b = self.manifest("b/core", ("a/core",))
        with self.assertRaises(ModuleRegistryError):
            circular.register_many([a, b])

    def test_tenant_entitlement_does_not_globally_enable_module(self):
        registry = ModuleRegistry()
        registry.register(self.manifest("sales/core"))
        registry.install("sales/core")
        registry.entitlements.grant(ModuleEntitlement("sales/core", "tenant-1"))

        with self.assertRaises(ModuleRegistryError):
            registry.require_tenant_enabled("tenant-1", "sales/core")
        self.assertFalse(registry.state("sales/core").enabled)

        registry.enable("sales/core")
        self.assertTrue(registry.is_available_for_tenant("tenant-1", "sales/core"))

    def test_expired_entitlement_is_denied(self):
        registry = ModuleRegistry()
        registry.register(self.manifest("sales/core"))
        registry.install("sales/core")
        registry.enable("sales/core")
        registry.entitlements.grant(
            ModuleEntitlement(
                "sales/core",
                "tenant-1",
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        )
        self.assertFalse(registry.is_available_for_tenant("tenant-1", "sales/core"))

    def test_disable_blocks_enabled_dependents(self):
        registry = ModuleRegistry()
        registry.register_many([
            self.manifest("sales/core"),
            self.manifest("sales/orders", ("sales/core",)),
        ])
        registry.enable("sales/core")
        registry.enable("sales/orders")
        with self.assertRaises(ModuleRegistryError):
            registry.disable("sales/core")

    def test_lifecycle_installs_before_enable(self):
        registry = ModuleRegistry()
        registry.register(self.manifest("sales/core"))
        ModuleLifecycle(registry).install_and_enable("sales/core")
        state = registry.state("sales/core")
        self.assertTrue(state.installed)
        self.assertTrue(state.enabled)

    def test_permission_declaration_and_event_contract(self):
        registry = ModuleRegistry()
        registry.register(self.manifest("sales/core", permissions=("sales.read",)))
        permissions = ModulePermissionService(registry)
        self.assertTrue(permissions.is_declared("sales/core", "sales.read"))
        self.assertFalse(permissions.is_declared("sales/core", "sales.write"))

        context = ModuleContext("tenant-1", "user-1", "request-1")
        event = ModuleEvent("sales.order.created", context, {"order_id": 10}, "sales/core")
        received = []
        bus = ModuleEventBus()
        bus.subscribe(event.name, received.append)
        bus.publish(event)
        self.assertEqual(received, [event])

    def test_discovery_returns_unique_sorted_manifests(self):
        manifests = discover_manifests(["app.modules.accounting", "app.modules.sales"])
        keys = [item.key for item in manifests]
        self.assertEqual(keys, sorted(set(keys)))


if __name__ == "__main__":
    unittest.main()
