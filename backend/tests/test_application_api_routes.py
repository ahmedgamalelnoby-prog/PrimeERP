import inspect

from main import create_application
from app.modules.documents.router import router as documents_router
from app.modules.helpdesk.router import router as helpdesk_router
from app.modules.project.router import router as project_router


def _openapi_paths():
    return create_application().openapi().get("paths", {})


def test_application_module_routes_are_registered():
    paths = _openapi_paths()
    assert "/api/v1/helpdesk/tickets" in paths
    assert "/api/v1/helpdesk/tickets/{ticket_id}/transition" in paths
    assert "/api/v1/projects/{project_id}/tasks" in paths
    assert "/api/v1/projects/{project_id}/task-dependencies" in paths
    assert "/api/v1/documents/{document_id}/versions" in paths
    assert "/api/v1/documents/{document_id}/shares" in paths


def test_application_module_routers_require_module_entitlements():
    expected_modules = (
        (helpdesk_router, "helpdesk"),
        (project_router, "project"),
        (documents_router, "documents"),
    )

    for router, module_code in expected_modules:
        assert router.dependencies
        dependency_bindings = [
            inspect.getclosurevars(dependency.dependency).nonlocals.get("canonical_code")
            for dependency in router.dependencies
        ]
        assert module_code in dependency_bindings
