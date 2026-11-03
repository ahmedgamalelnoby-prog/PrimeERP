from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.core.context import RequestContext, reset_request_context, set_request_context
from app.modules.companies.access import accessible_company_query, require_company_access


def _compile(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_regular_user_company_query_requires_explicit_assignment():
    token = set_request_context(RequestContext(request_id="company-access", tenant_id=42))
    try:
        user = SimpleNamespace(id=7, tenant_id=42, is_platform_admin=False)
        sql = _compile(accessible_company_query(user))
        assert "user_company_access" in sql
        assert "user_company_access.user_id = 7" in sql
        assert "companies.tenant_id = 42" in sql
        assert "companies.is_active IS true" in sql
    finally:
        reset_request_context(token)


def test_platform_admin_company_query_uses_selected_tenant_without_membership_join():
    token = set_request_context(RequestContext(request_id="platform-company-access", tenant_id=9))
    try:
        user = SimpleNamespace(id=1, tenant_id=None, is_platform_admin=True)
        sql = _compile(accessible_company_query(user))
        assert "companies.tenant_id = 9" in sql
        assert "user_company_access" not in sql
    finally:
        reset_request_context(token)


def test_inactive_companies_can_be_requested_only_when_explicitly_allowed():
    token = set_request_context(RequestContext(request_id="inactive-company-access", tenant_id=42))
    try:
        user = SimpleNamespace(id=7, tenant_id=42, is_platform_admin=False)
        active_sql = _compile(accessible_company_query(user))
        all_sql = _compile(accessible_company_query(user, active_only=False))
        assert "companies.is_active IS true" in active_sql
        assert "AND companies.is_active IS true" not in all_sql
    finally:
        reset_request_context(token)


def test_require_company_access_fails_closed_for_unassigned_company():
    token = set_request_context(RequestContext(request_id="company-access-denied", tenant_id=42))
    try:
        user = SimpleNamespace(id=7, tenant_id=42, is_platform_admin=False)

        class EmptyDB:
            def scalar(self, _statement):
                return None

        with pytest.raises(HTTPException) as exc:
            require_company_access(EmptyDB(), user, 999)
        assert exc.value.status_code == 404
    finally:
        reset_request_context(token)
