from app.core.module_engine.manifest import ModuleManifest
from app.core.module_engine.registry import ModuleRegistry, ModuleRegistryError


def module(name: str, *dependencies: str) -> ModuleManifest:
    return ModuleManifest(
        technical_name=name,
        display_name=name,
        dependencies=dependencies,
    )


def test_registry_accepts_dependency_order_independently() -> None:
    registry = ModuleRegistry()
    registry.register_many(
        [
            module("sales/orders", "sales/core"),
            module("sales/core"),
        ]
    )
    registry.enable("sales/core")
    registry.enable("sales/orders")


def test_registry_rejects_missing_dependency() -> None:
    registry = ModuleRegistry()
    registry.register(module("sales/orders", "sales/core"))
    try:
        registry.validate_graph()
    except ModuleRegistryError as exc:
        assert "sales/core" in str(exc)
    else:
        raise AssertionError("missing dependency was not rejected")


def test_registry_rejects_circular_dependencies() -> None:
    registry = ModuleRegistry()
    registry.register_many(
        [
            module("a/core", "b/core"),
            module("b/core", "a/core"),
        ]
    )
    try:
        registry.validate_graph()
    except ModuleRegistryError as exc:
        assert "Circular" in str(exc)
    else:
        raise AssertionError("circular dependency was not rejected")


def test_registry_prevents_disabling_a_required_dependency() -> None:
    registry = ModuleRegistry()
    registry.register_many([module("sales/core"), module("sales/orders", "sales/core")])
    registry.enable("sales/core")
    registry.enable("sales/orders")
    try:
        registry.disable("sales/core")
    except ModuleRegistryError as exc:
        assert "sales/orders" in str(exc)
    else:
        raise AssertionError("required dependency was disabled")
