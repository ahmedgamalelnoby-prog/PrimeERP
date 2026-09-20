from types import SimpleNamespace

from app.modules.audit.service import record_audit_event


def test_audit_event_can_be_recorded_without_http_request_context():
    captured = {}

    class FakeDB:
        def add(self, value):
            captured["event"] = value

    event = record_audit_event(
        FakeDB(),
        action="commerce.payment.post",
        entity_type="commerce_payment",
        entity_id=77,
        user_id=None,
        tenant_id=3,
        company_id=7,
        metadata={"amount": "1140.00"},
    )

    assert captured["event"] is event
    assert event.entity_id == "77"
    assert event.tenant_id == 3
    assert event.company_id == 7
    assert event.request_id is None


def test_audit_event_prefers_explicit_scope_over_request_context(monkeypatch):
    from app.core.context.manager import set_request_context, reset_request_context
    from app.core.context.request_context import RequestContext

    token = set_request_context(RequestContext(request_id="req-1", user_id=11, company_id=99))
    try:
        class FakeDB:
            def add(self, value):
                self.event = value

        db = FakeDB()
        event = record_audit_event(
            db,
            action="test.action",
            entity_type="test",
            user_id=22,
            company_id=7,
        )
        assert event.user_id == 22
        assert event.company_id == 7
        assert event.request_id == "req-1"
    finally:
        reset_request_context(token)
