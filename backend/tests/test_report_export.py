import json

import pytest
from fastapi import HTTPException

from app.modules.reports import router as reports_router
from app.modules.reports.router import _render_export


def test_json_export_respects_filter_policy():
    body, media_type = _render_export(
        title="Sales", rows=[{"invoice": "INV-1"}],
        filters={"branch_id": 3}, export_format="json", include_filters=True,
    )
    payload = json.loads(body)
    assert media_type.startswith("application/json")
    assert payload["filters"] == {"branch_id": 3}
    assert payload["row_count"] == 1


def test_json_export_omits_filters_when_disabled():
    body, _ = _render_export(
        title="Sales", rows=[], filters={"branch_id": 3},
        export_format="json", include_filters=False,
    )
    assert "filters" not in json.loads(body)


def test_text_export_formats_rows_and_omits_disabled_filters():
    body, media_type = _render_export(
        title="Sales", rows=[{"invoice": "INV-1", "amount": 120}],
        filters={"branch_id": 3}, export_format="text", include_filters=False,
    )
    assert media_type.startswith("text/plain")
    assert "INV-1" in body
    assert "amount: 120" in body
    assert "branch_id" not in body


def test_export_rejects_unsupported_format():
    with pytest.raises(HTTPException) as exc:
        _render_export(
            title="Sales", rows=[], filters={}, export_format="csv",
            include_filters=True,
        )
    assert exc.value.status_code == 500



def test_export_module_access_requires_tenant_entitlement_and_user_permission(monkeypatch):
    user = object()
    monkeypatch.setattr(reports_router, "get_effective_tenant_id", lambda current: 9)
    monkeypatch.setattr(reports_router, "tenant_has_module", lambda db, tenant_id, module: True)
    monkeypatch.setattr(reports_router, "user_has_permission", lambda current, permission, db: True)
    assert reports_router._require_export_module_access(None, user, "accounting") is None


def test_export_module_access_denies_module_without_entitlement(monkeypatch):
    user = object()
    monkeypatch.setattr(reports_router, "get_effective_tenant_id", lambda current: 9)
    monkeypatch.setattr(reports_router, "tenant_has_module", lambda db, tenant_id, module: False)
    monkeypatch.setattr(reports_router, "user_has_permission", lambda current, permission, db: True)
    with pytest.raises(HTTPException) as exc:
        reports_router._require_export_module_access(None, user, "accounting")
    assert exc.value.status_code == 403


def test_export_module_access_denies_user_without_owner_module_permission(monkeypatch):
    user = object()
    monkeypatch.setattr(reports_router, "get_effective_tenant_id", lambda current: 9)
    monkeypatch.setattr(reports_router, "tenant_has_module", lambda db, tenant_id, module: True)
    monkeypatch.setattr(reports_router, "user_has_permission", lambda current, permission, db: False)
    with pytest.raises(HTTPException) as exc:
        reports_router._require_export_module_access(None, user, "accounting")
    assert exc.value.status_code == 403
