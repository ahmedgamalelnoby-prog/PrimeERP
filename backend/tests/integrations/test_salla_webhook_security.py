import hashlib

from app.modules.integrations.router import _event_identity


def test_event_identity_prefers_explicit_event_id():
    payload = {"event": "order.created", "data": {"id": 123}}
    external_id, event_type = _event_identity(payload, None, "delivery-42", b'{"event":"order.created"}')

    assert external_id == "delivery-42"
    assert event_type == "order.created"


def test_event_identity_does_not_use_business_object_id_as_delivery_key():
    raw = b'{"event":"order.created","data":{"id":123}}'
    payload = {"event": "order.created", "data": {"id": 123}}

    external_id, event_type = _event_identity(payload, None, None, raw)

    expected = "sha256:" + hashlib.sha256(b"order.created\n" + raw).hexdigest()
    assert external_id == expected
    assert external_id != "123"
    assert event_type == "order.created"


def test_event_identity_requires_event_type():
    try:
        _event_identity({"data": {"id": 123}}, None, None, b"{}")
    except Exception as exc:
        assert "event type" in str(exc.detail).lower()
    else:
        raise AssertionError("Expected webhook event type validation to fail")
