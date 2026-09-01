from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlalchemy.orm import configure_mappers

from app.database import models as database_models  # noqa: F401
from app.modules.identity.models.user import User
from app.modules.roles.models import Role
from main import create_application


def _application() -> FastAPI:
    """Build the application through the production application factory."""
    return create_application()


def _routes(application: FastAPI) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in application.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }


def test_sqlalchemy_mappers_configure() -> None:
    configure_mappers()
    assert User.__tablename__ == "users"
    assert Role.__tablename__ == "roles"


def test_identity_auth_routes_are_registered_once() -> None:
    application = _application()
    routes = _routes(application)

    assert ("POST", "/api/v1/identity/login") in routes
    assert ("POST", "/api/v1/identity/refresh") in routes
    assert ("GET", "/api/v1/identity/me") in routes
    assert sum(
        1
        for method, path in routes
        if method == "POST" and path == "/api/v1/identity/login"
    ) == 1


def test_system_health_and_openapi_routes_exist() -> None:
    application = _application()
    routes = _routes(application)

    assert ("GET", "/health") in routes
    assert (
        ("GET", "/api/v1/openapi.json") in routes
        or application.openapi_url == "/api/v1/openapi.json"
    )
