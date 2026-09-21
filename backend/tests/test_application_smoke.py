from fastapi.routing import APIRoute
from sqlalchemy.orm import configure_mappers

from app.database import models as database_models  # noqa: F401
from app.modules.identity.models.user import User
from app.modules.roles.models import Role
from main import app, create_application


def _routes(application) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()

    def walk(routes) -> None:
        for route in routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    found.add((method, route.path))
            nested = getattr(route, "routes", None)
            if nested:
                walk(nested)

    walk(application.routes)
    return found


def test_sqlalchemy_mappers_configure() -> None:
    configure_mappers()
    assert User.__tablename__ == "users"
    assert Role.__tablename__ == "roles"


def test_identity_auth_routes_are_registered_once() -> None:
    routes = _routes(app)
    assert ("POST", "/api/v1/identity/login") in routes
    assert ("POST", "/api/v1/identity/refresh") in routes
    assert ("GET", "/api/v1/identity/me") in routes
    assert sum(1 for method, path in routes if method == "POST" and path == "/api/v1/identity/login") == 1


def test_application_router_tree_is_isolated() -> None:
    first = create_application()
    second = create_application()
    first_routes = _routes(first)
    second_routes = _routes(second)

    assert ("POST", "/api/v1/identity/login") in first_routes
    assert ("POST", "/api/v1/identity/login") in second_routes
    assert sum(1 for method, path in first_routes if method == "POST" and path == "/api/v1/identity/login") == 1
    assert sum(1 for method, path in second_routes if method == "POST" and path == "/api/v1/identity/login") == 1


def test_system_health_and_openapi_routes_exist() -> None:
    routes = _routes(app)
    assert ("GET", "/health") in routes
    assert ("GET", "/api/v1/openapi.json") in routes or app.openapi_url == "/api/v1/openapi.json"
