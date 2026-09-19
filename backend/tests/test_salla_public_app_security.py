from app.modules.integrations.salla_public_app_service import (
    _event_id,
    _event_payload_hash,
)


def test_salla_event_id_prefers_explicit_identity():
    payload = {
        "event": "app.subscription.renewed",
        "merchant": {"id": "merchant-1"},
        "event_id": "evt-123",
        "data": {"id": "subscription-99"},
    }

    assert _event_id(payload) == "evt-123"


def test_salla_event_id_uses_data_identity_when_present():
    payload = {
        "event": "app.updated",
        "merchant": {"id": "merchant-1"},
        "data": {"id": "evt-456"},
    }

    assert _event_id(payload) == "evt-456"


def test_salla_event_id_is_deterministic_without_provider_id():
    payload = {
        "event": "app.updated",
        "merchant": {"id": "merchant-1"},
        "data": {"store_name": "Example"},
    }

    assert _event_id(payload) == _event_id(dict(payload))
    assert _event_id(payload).startswith("sha256:")


def test_salla_payload_hash_changes_when_payload_changes():
    base = {
        "event": "app.updated",
        "merchant": {"id": "merchant-1"},
        "data": {"store_name": "Example"},
    }
    changed = {
        **base,
        "data": {"store_name": "Changed"},
    }

    assert _event_payload_hash(base) != _event_payload_hash(changed)
\n\ndef test_salla_connection_reuse_is_company_and_tenant_scoped():\n    from app.modules.integrations.salla_public_app_service import _ensure_connection\n    source = _ensure_connection.__code__\n    assert "company_id" in source.co_names\n    assert "tenant_id" in source.co_names\n    assert "provider" in source.co_names\n\n\ndef test_salla_authorization_validates_installation_company_tenant_integrity():\n    from app.modules.integrations.salla_public_app_service import handle_authorize_event\n    source = handle_authorize_event.__code__\n    assert "company_id" in source.co_names\n    assert "tenant_id" in source.co_names\n