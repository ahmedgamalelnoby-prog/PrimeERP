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
    for router in (helpdesk_router, project_router, documents_router):
        assert router.dependencies
        assert any(getattr(dependency.dependency, "__name__", "") == "require_module" for dependency in router.dependencies)
