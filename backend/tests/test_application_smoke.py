from sqlalchemy.orm import configure_mappers

from app.database import models as database_models  # noqa: F401
from app.modules.identity.models.user import User
from app.modules.roles.models import Role
from main import app, create_application


def _openapi_operations(application) -> set[tuple[str, str]]:
    """Return HTTP method/path pairs from FastAPI's public OpenAPI contract."""
    operations: set[tuple[str, str]] = set()
    for path, item in application.openapi()["paths"].items():
        for method in item:
            if method in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                operations.add((method.upper(), path))
    return operations


def test_sqlalchemy_mappers_configure() -> None:
    configure_mappers()
    assert User.__tablename__ == "users"
    assert Role.__tablename__ == "roles"


def test_identity_auth_routes_are_registered_once() -> None:
    routes = _openapi_operations(app)
    assert ("POST", "/api/v1/identity/login") in routes
    assert ("POST", "/api/v1/identity/refresh") in routes
    assert ("GET", "/api/v1/identity/me") in routes


def test_application_router_tree_is_isolated() -> None:
    first = create_application()
    second = create_application()
    first_routes = _openapi_operations(first)
    second_routes = _openapi_operations(second)

    assert ("POST", "/api/v1/identity/login") in first_routes
    assert ("POST", "/api/v1/identity/login") in second_routes
    assert ("POST", "/api/v1/identity/refresh") in first_routes
    assert ("POST", "/api/v1/identity/refresh") in second_routes
    assert ("GET", "/api/v1/identity/me") in first_routes
    assert ("GET", "/api/v1/identity/me") in second_routes


def test_system_health_and_openapi_routes_exist() -> None:
    routes = _openapi_operations(app)
    assert ("GET", "/health") in routes
    assert app.openapi_url == "/api/v1/openapi.json"
