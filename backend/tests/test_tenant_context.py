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
