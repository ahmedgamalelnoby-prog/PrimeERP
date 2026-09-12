from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from app.core.module_engine.contracts import ModuleManifest
from app.core.module_engine.entitlement import ModuleEntitlement
from app.core.module_engine.registry import ModuleRegistry
from app.core.module_engine.errors import ModuleRegistryError


class ModuleEngineTests(unittest.TestCase):
    def test_tenant_entitlement_does_not_globally_enable(self) -> None:
        registry = ModuleRegistry()
        module = ModuleManifest("test/core", "Core")
        registry.register(module)
        registry.install("test/core")
        registry.enable("test/core")
        registry.entitlements.grant(
            ModuleEntitlement(technical_name="test/core", tenant_id="tenant-1")
        )
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
                technical_name="test/core",
                tenant_id="tenant-1",
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        self.assertFalse(registry.is_available_for_tenant("tenant-1", "test/core"))

    def test_disabled_entitlement(self) -> None:
        registry = ModuleRegistry()
        module = ModuleManifest("test/core", "Core")
        registry.register(module)
        registry.install("test/core")
        registry.enable("test/core")
        registry.entitlements.grant(
            ModuleEntitlement(
                technical_name="test/core",
                tenant_id="tenant-1",
                enabled=False,
            )
        )
        self.assertFalse(registry.is_available_for_tenant("tenant-1", "test/core"))

    def test_revoke(self) -> None:
        registry = ModuleRegistry()
        module = ModuleManifest("test/core", "Core")
        registry.register(module)
        registry.install("test/core")
        registry.enable("test/core")
        registry.entitlements.grant(
            ModuleEntitlement(technical_name="test/core", tenant_id="tenant-1")
        )
        registry.entitlements.revoke("tenant-1", "test/core")
        self.assertFalse(registry.is_available_for_tenant("tenant-1", "test/core"))

    def test_unknown_module(self) -> None:
        registry = ModuleRegistry()
        self.assertFalse(registry.is_available_for_tenant("tenant-1", "missing/module"))

    def test_cannot_enable_uninstalled_module(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/core", "Core"))
        with self.assertRaises(ModuleRegistryError):
            registry.enable("test/core")

    def test_duplicate_registration(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/core", "Core"))
        with self.assertRaises(ModuleRegistryError):
            registry.register(ModuleManifest("test/core", "Core"))

    def test_dependency_must_exist(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/app", "App", dependencies=("test/core",)))
        with self.assertRaises(ModuleRegistryError):
            registry.validate_graph()

    def test_circular_dependency(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/a", "A", dependencies=("test/b",)))
        registry.register(ModuleManifest("test/b", "B", dependencies=("test/a",)))
        with self.assertRaises(ModuleRegistryError):
            registry.validate_graph()

    def test_install_dependency(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/core", "Core"))
        registry.register(ModuleManifest("test/app", "App", dependencies=("test/core",)))
        registry.install("test/core")
        registry.install("test/app")
        self.assertTrue(registry.state("test/core").installed)
        self.assertTrue(registry.state("test/app").installed)

    def test_enable_dependency(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/core", "Core"))
        registry.register(ModuleManifest("test/app", "App", dependencies=("test/core",)))
        registry.install("test/core")
        registry.install("test/app")
        registry.enable("test/core")
        registry.enable("test/app")
        self.assertTrue(registry.state("test/app").enabled)

    def test_disable(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/core", "Core"))
        registry.install("test/core")
        registry.enable("test/core")
        registry.disable("test/core")
        self.assertFalse(registry.state("test/core").enabled)

    def test_uninstall(self) -> None:
        registry = ModuleRegistry()
        registry.register(ModuleManifest("test/core", "Core"))
        registry.install("test/core")
        registry.enable("test/core")
        registry.uninstall("test/core")
        self.assertFalse(registry.state("test/core").installed)

    def test_permissions_are_declared(self) -> None:
        registry = ModuleRegistry()
        registry.register(
            ModuleManifest("test/core", "Core", permissions=("test.read", "test.write"))
        )
        self.assertTrue(registry.is_declared_permission("test.read"))
        self.assertFalse(registry.is_declared_permission("missing.read"))


if __name__ == "__main__":
    unittest.main()
