from fastapi import FastAPI

from app.api.v1.router import build_router


def _application_routes():
    app = FastAPI()
    app.include_router(build_router())
    return [route for route in app.routes if hasattr(route, "path")]


def _paths(prefix: str) -> set[str]:
    return {route.path for route in _application_routes() if route.path.startswith(prefix)}


def test_application_module_routes_are_registered():
    assert "/helpdesk/tickets" in _paths("/helpdesk")
    assert "/helpdesk/tickets/{ticket_id}/transition" in _paths("/helpdesk")
    assert "/projects/{project_id}/tasks" in _paths("/projects")
    assert "/projects/{project_id}/task-dependencies" in _paths("/projects")
    assert "/documents/{document_id}/versions" in _paths("/documents")
    assert "/documents/{document_id}/shares" in _paths("/documents")


def test_application_routes_have_module_entitlement_dependencies():
    module_routes = [
        route
        for route in _application_routes()
        if route.path.startswith(("/helpdesk", "/projects", "/documents"))
    ]
    assert module_routes
    assert all(route.dependant.dependencies for route in module_routes)
