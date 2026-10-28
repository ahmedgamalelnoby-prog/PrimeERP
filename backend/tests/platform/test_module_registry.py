from app.modules.identity.dependencies import get_current_user
from fastapi.testclient import TestClient

from app.modules.platform.api.router import router as module_registry_router
from main import app
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


def test_module_registry_api_requires_authenticated_user_dependency():
    protected_routes = {
        route.path: route
        for route in module_registry_router.routes
        if getattr(route, "methods", None) and "GET" in route.methods
    }

    assert set(protected_routes) == {"/platform/modules", "/platform/modules/{module_key}"}
    for route in protected_routes.values():
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        assert get_current_user in dependency_calls


def test_module_registry_api_rejects_requests_without_access_token():
    client = TestClient(app)

    for path in ("/api/v1/platform/modules", "/api/v1/platform/modules/accounting"):
        response = client.get(path)
        assert response.status_code == 401, (path, response.status_code, response.text)
