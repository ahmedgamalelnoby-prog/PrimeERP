from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import configure_mappers

from app.core.context import RequestContext, clear_request_context, reset_request_context, set_request_context
from app.core.context.tenant import get_effective_tenant_id
from app.database import models as database_models  # noqa: F401
from app.modules.identity.models.user import User
from app.modules.roles.models import Role
from main import app, create_application


def _openapi_paths(application) -> dict:
    return application.openapi().get("paths", {})


def _user(tenant_id=None):
    return SimpleNamespace(tenant_id=tenant_id)


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

    assert first_paths["/api/v1/identity/login"] == second_paths["/api/v1/identity/login"]


def test_system_health_and_openapi_routes_exist() -> None:
    paths = _openapi_paths(app)
    assert "/health" in paths
    assert app.openapi_url == "/api/v1/openapi.json"


def test_cors_allows_platform_tenant_context_header() -> None:
    cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    allow_headers = {str(header).lower() for header in cors.kwargs["allow_headers"]}
    assert "x-tenant-id" in allow_headers


def test_platform_admin_uses_request_tenant_without_mutating_user_tenant() -> None:
    token = set_request_context(RequestContext(request_id="tenant-context-test", tenant_id=42))
    try:
        user = _user(None)
        assert get_effective_tenant_id(user) == 42
        assert user.tenant_id is None
    finally:
        reset_request_context(token)


def test_regular_user_uses_authenticated_tenant_when_context_is_empty() -> None:
    token = set_request_context(RequestContext(request_id="tenant-context-test"))
    try:
        assert get_effective_tenant_id(_user(7)) == 7
    finally:
        reset_request_context(token)


def test_missing_tenant_context_is_rejected() -> None:
    token = set_request_context(RequestContext(request_id="tenant-context-test"))
    try:
        with pytest.raises(HTTPException) as exc:
            get_effective_tenant_id(_user(None))
        assert exc.value.status_code == 400
        assert exc.value.detail == "Tenant context is required for this operation"
    finally:
        reset_request_context(token)
        clear_request_context()
