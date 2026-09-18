from app.modules.platform.module_registry import REGISTRY_VERSION, get_module, list_modules


def test_module_registry_is_versioned_and_unique():
    modules = list_modules()
    assert REGISTRY_VERSION
    assert modules
    keys = [str(item["key"]) for item in modules]
    assert len(keys) == len(set(keys))


def test_module_registry_lookup():
    accounting = get_module("accounting")
    assert accounting is not None
    assert accounting["name"] == "Accounting"
    assert get_module("does-not-exist") is None
