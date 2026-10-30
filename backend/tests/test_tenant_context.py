from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.context import RequestContext, get_effective_tenant_id, set_request_context, reset_request_context


def _user(*, tenant_id=None, is_platform_admin=False):
    return SimpleNamespace(tenant_id=tenant_id, is_platform_admin=is_platform_admin)


def test_regular_user_uses_bound_tenant():
    token = set_request_context(RequestContext(request_id="test", tenant_id=42))
    try:
        assert get_effective_tenant_id(_user(tenant_id=42)) == 42
    finally:
        reset_request_context(token)


def test_platform_admin_uses_selected_request_tenant():
    token = set_request_context(RequestContext(request_id="test", tenant_id=7))
    try:
        assert get_effective_tenant_id(_user(is_platform_admin=True)) == 7
    finally:
        reset_request_context(token)


def test_platform_admin_without_context_is_rejected():
    token = set_request_context(RequestContext(request_id="test"))
    try:
        with pytest.raises(HTTPException) as exc:
            get_effective_tenant_id(_user(is_platform_admin=True))
        assert exc.value.status_code == 400
    finally:
        reset_request_context(token)


def test_regular_user_without_tenant_is_rejected():
    token = set_request_context(RequestContext(request_id="test"))
    try:
        with pytest.raises(HTTPException) as exc:
            get_effective_tenant_id(_user())
        assert exc.value.status_code == 403
    finally:
        reset_request_context(token)


def _request_with_headers(headers: dict[str, str]) -> Request:
    scope = {"type": "http", "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()]}
    return Request(scope)


def test_request_context_reads_selected_tenant_header():
    from app.core.middleware.request_context import RequestContextMiddleware
    middleware = object.__new__(RequestContextMiddleware)
    request = _request_with_headers({"X-Tenant-ID": "17"})
    assert middleware._resolve_tenant_id(request) == 17


def test_request_context_rejects_invalid_tenant_header():
    from app.core.middleware.request_context import RequestContextMiddleware
    middleware = object.__new__(RequestContextMiddleware)
    request = _request_with_headers({"X-Tenant-ID": "not-a-number"})
    assert middleware._resolve_tenant_id(request) is None


def test_regular_user_cannot_override_authenticated_tenant_with_header(monkeypatch):
    from app.modules.identity.dependencies import current_user as auth_dependencies

    user = _user(tenant_id=42)
    user.id = 9
    user.username = "tenant-user"
    user.is_deleted = False
    user.is_active = True
    user.role_id = None

    monkeypatch.setattr(
        auth_dependencies.token_service,
        "decode_token",
        lambda token, expected_type: {"user_id": 9, "tenant_id": 42},
    )
    monkeypatch.setattr(
        auth_dependencies.user_repository,
        "get_by_id",
        lambda db, user_id: user,
    )
    token = set_request_context(RequestContext(request_id="test", tenant_id=99))
    try:
        with pytest.raises(HTTPException) as exc:
            auth_dependencies._authenticate_user("valid-token", object(), "99")
        assert exc.value.status_code == 403
        assert exc.value.detail == "Tenant context does not match the authenticated user"
    finally:
        reset_request_context(token)


def test_regular_user_token_tenant_must_match_database_assignment(monkeypatch):
    from app.modules.identity.dependencies import current_user as auth_dependencies

    user = _user(tenant_id=42)
    user.id = 9
    user.username = "tenant-user"
    user.is_deleted = False
    user.is_active = True
    user.role_id = None

    monkeypatch.setattr(
        auth_dependencies.token_service,
        "decode_token",
        lambda token, expected_type: {"user_id": 9, "tenant_id": 99},
    )
    monkeypatch.setattr(
        auth_dependencies.user_repository,
        "get_by_id",
        lambda db, user_id: user,
    )
    token = set_request_context(RequestContext(request_id="test", tenant_id=42))
    try:
        with pytest.raises(HTTPException) as exc:
            auth_dependencies._authenticate_user("forged-tenant-token", object(), None)
        assert exc.value.status_code == 401
    finally:
        reset_request_context(token)
