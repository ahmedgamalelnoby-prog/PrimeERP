from datetime import datetime, timedelta, timezone
import unittest

from app.core.module_engine import (
    DEFAULT_MODULE_PACKAGE,
    ModuleArchitectureError,
    ModuleContext,
    ModuleEntitlement,
    ModuleEvent,
    ModuleEventBus,
    ModuleManifest,
    ModulePermissionService,
    ModuleRegistry,
    ModuleRegistryError,
    bootstrap_module_registry,
    catalog,
    validate_catalog_dependencies,
    validate_manifests,
)
from app.core.module_engine.discovery import discover_manifests
from app.core.module_engine.lifecycle import ModuleLifecycle


class ModuleEngineTests(unittest.TestCase):
    def test_dependency_order(self) -> None:
        registry = ModuleRegistry()
        core = ModuleManifest("test/core", "Core")
        feature = ModuleManifest("test/feature", "Feature", dependencies=("test/core",))
        registry.register_many([feature, core])
        registry.install("test/core")
        registry.enable("test/core")
        registry.install("test/feature")
        registry.enable("test/feature")
        self.assertTrue(registry.state("test/feature").enabled)

    def test_missing_dependency(self) -> None:
        with self.assertRaises(ModuleArchitectureError):
            validate_manifests([ModuleManifest("test/feature", "Feature", dependencies=("test/missing",))])

    def test_circular_dependencies(self) -> None:
        registry = ModuleRegistry()
        a = ModuleManifest("test/a", "A", dependencies=("test/b",))
        b = ModuleManifest("test/b", "B", dependencies=("test/a",))
        with self.assertRaises(ModuleRegistryError):
            registry.register_many([a, b])

    def test_tenant_entitlement_does_not_globally_enable(self) -> None:
        registry = ModuleRegistry()
        module = ModuleManifest("test/core", "Core")
        registry.register(module)
        registry.install("test/core")
        registry.enable("test/core")
        registry.entitlements.grant(ModuleEntitlement("tenant-1", "test/core"))
        self.assertTrue(registry.is_available_for_tenant("tenant-1", "test/core"))
        self.assertFalse(registry.is_available_for_tenant("tenant-2", "test/core"))
        self.assertTrue(registry.state("test/core").enabled)

    def test_expiry(self) -> None:
        registry = ModuleRegistry()
        module = ModuleManifest("test/core", "Core")
        registry.register(module)
        registry.install("test/core")
        registry.enable("test/core")
        registry.entitlements.grant(
            ModuleEntitlement(
                "tenant-1",
                "test/core",
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        self.assertFalse(registry.is_available_for_tenant("tenant-1", "test/core"))

    def test_disable_blocked_by_dependents(self) -> None:
        registry = ModuleRegistry()
        registry.register_many([
            ModuleManifest("test/core", "Core"),
            ModuleManifest("test/feature", "Feature", dependencies=("test/core",)),
        ])
        registry.install("test/core")
        registry.enable("test/core")
        registry.install("test/feature")
        registry.enable("test/feature")
        with self.assertRaises(ModuleRegistryError):
            registry.disable("test/core")

    def test_lifecycle_install_enable(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/core", "Core"))
        ModuleLifecycle(registry).install_and_enable("test/core")
        self.assertTrue(registry.state("test/core").enabled)

    def test_permissions(self) -> None:
        service = ModulePermissionService()
        manifest = ModuleManifest("test/core", "Core", permissions=frozenset({"test.read"}))
        service.validate_manifest(manifest)
        with self.assertRaises(ValueError):
            service.validate_manifest(ModuleManifest("test/invalid", "Invalid", permissions=frozenset({""})))

    def test_event_bus(self) -> None:
        bus = ModuleEventBus()
        events: list[ModuleEvent] = []
        bus.subscribe("test.created", events.append)
        bus.publish(ModuleEvent("test.created", ModuleContext("tenant-1", "user-1"), {"id": 1}))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["id"], 1)

    def test_discovery_deduplicates_and_sorts(self) -> None:
        manifests = discover_manifests(("app.modules.accounting", "app.modules.sales"))
        keys = [item.key for item in manifests]
        self.assertEqual(keys, sorted(set(keys)))

    def test_catalog_consistency(self) -> None:
        validate_catalog_dependencies()
        self.assertGreater(len(catalog()), 10)

    def test_strict_manifest_validation(self) -> None:
        with self.assertRaises(ModuleArchitectureError):
            validate_manifests([ModuleManifest("test/unknown", "Unknown")], strict_catalog=True)

    def test_default_bootstrap_is_rooted_at_all_modules(self) -> None:
        registry = bootstrap_module_registry()
        self.assertTrue(registry.all())
        self.assertEqual(DEFAULT_MODULE_PACKAGE, "app.modules")
        self.assertTrue(any(item.key.startswith("accounting/") for item in registry.all()))

    def test_canonical_journal_boundary_is_discovered_once(self) -> None:
        manifests = discover_manifests(("app.modules.accounting",))
        matches = [item for item in manifests if item.key == "accounting/journal_entries"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].version, "1.0.1")
        self.assertIn("accounting/chart_of_accounts", matches[0].dependencies)


if __name__ == "__main__":
    unittest.main()
