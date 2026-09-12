from sqlalchemy.orm import configure_mappers

from app.database import models as database_models  # noqa: F401
from app.modules.identity.models.user import User
from app.modules.roles.models import Role
from main import app, create_application


def _openapi_paths(application) -> dict:
    return application.openapi().get("paths", {})


def test_sqlalchemy_mappers_configure() -> None:
    configure_mappers()
    assert User.__tablename__ == "users"
    assert Role.__tablename__ == "roles"


def test_identity_auth_routes_are_registered_once() -> None:
    paths = _openapi_paths(app)

    assert "/api/v1/identity/login" in paths
    assert "/api/v1/identity/refresh" in paths
    assert "/api/v1/identity/me" in paths

    login_operations = paths["/api/v1/identity/login"]
    assert list(login_operations).count("post") == 1
    assert login_operations["post"]["operationId"] == "login_api_v1_identity_login_post"


def test_application_router_tree_is_isolated() -> None:
    first = create_application()
    second = create_application()
    first_paths = _openapi_paths(first)
    second_paths = _openapi_paths(second)

    for paths in (first_paths, second_paths):
        assert "/api/v1/identity/login" in paths
        assert "/api/v1/identity/refresh" in paths
        assert "/api/v1/identity/me" in paths
        assert list(paths["/api/v1/identity/login"]).count("post") == 1
        assert (
            paths["/api/v1/identity/login"]["post"]["operationId"]
            == "login_api_v1_identity_login_post"
        )

    # Creating a second application must not mutate the first application's
    # OpenAPI route tree or introduce duplicate identity operations.
    assert first_paths["/api/v1/identity/login"] == second_paths["/api/v1/identity/login"]


def test_system_health_and_openapi_routes_exist() -> None:
    paths = _openapi_paths(app)
    assert "/health" in paths
    assert app.openapi_url == "/api/v1/openapi.json"
