from app.api.v1.router import build_router


def _paths(prefix: str) -> set[str]:
    return {route.path for route in build_router().routes if route.path.startswith(prefix)}


def test_application_module_routes_are_registered():
    assert "/helpdesk/tickets" in _paths("/helpdesk")
    assert "/helpdesk/tickets/{ticket_id}/transition" in _paths("/helpdesk")
    assert "/projects/{project_id}/tasks" in _paths("/projects")
    assert "/projects/{project_id}/task-dependencies" in _paths("/projects")
    assert "/documents/{document_id}/versions" in _paths("/documents")
    assert "/documents/{document_id}/shares" in _paths("/documents")


def test_application_routes_have_module_entitlement_dependencies():
    router = build_router()
    module_paths = {
        route.path: route for route in router.routes
        if route.path.startswith(("/helpdesk", "/projects", "/documents"))
    }
    assert all(route.dependant.dependencies for route in module_paths.values())
