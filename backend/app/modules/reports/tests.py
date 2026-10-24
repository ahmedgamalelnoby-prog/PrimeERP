from fastapi import HTTPException
import pytest

from app.modules.reports import router


def test_schedule_policy_blocks_delivery_when_company_disables_it(monkeypatch):
    monkeypatch.setattr(router, "policy", lambda db, company_id, key: False)
    with pytest.raises(HTTPException) as exc:
        router._resolve_schedule_format(None, 7, None)
    assert exc.value.status_code == 409
    assert "disabled by company policy" in exc.value.detail


def test_schedule_policy_uses_company_default_format(monkeypatch):
    values = {
        "reports.allow_scheduled_delivery": True,
        "reports.default_export_format": "text",
    }
    monkeypatch.setattr(router, "policy", lambda db, company_id, key: values[key])
    assert router._resolve_schedule_format(None, 7, None) == "text"


def test_schedule_policy_preserves_explicit_supported_format(monkeypatch):
    monkeypatch.setattr(
        router,
        "policy",
        lambda db, company_id, key: True if key == "reports.allow_scheduled_delivery" else "json",
    )
    assert router._resolve_schedule_format(None, 7, "text") == "text"


@pytest.mark.parametrize("bad_default", ["xlsx", "csv", None, True])
def test_schedule_policy_fails_closed_for_invalid_saved_default(monkeypatch, bad_default):
    monkeypatch.setattr(
        router,
        "policy",
        lambda db, company_id, key: True if key == "reports.allow_scheduled_delivery" else bad_default,
    )
    with pytest.raises(HTTPException) as exc:
        router._resolve_schedule_format(None, 7, None)
    assert exc.value.status_code == 500


def test_schedule_policy_fails_closed_for_non_boolean_enable_switch(monkeypatch):
    monkeypatch.setattr(router, "policy", lambda db, company_id, key: "true")
    with pytest.raises(HTTPException) as exc:
        router._resolve_schedule_format(None, 7, None)
    assert exc.value.status_code == 500
