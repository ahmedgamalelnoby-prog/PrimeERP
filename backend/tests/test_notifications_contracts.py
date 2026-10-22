import pytest
from pydantic import ValidationError

from app.modules.notifications.router import _render
from app.modules.notifications.schemas import GroupUpsert, SendNotificationRequest, TemplateUpsert


def test_notification_template_render_uses_only_named_context_values():
    assert _render("Invoice {{ invoice_no }} total {{ total }} {{ missing }}", {
        "invoice_no": "INV-10",
        "total": 125.5,
    }) == "Invoice INV-10 total 125.5 "


def test_notification_group_rejects_duplicate_destinations():
    with pytest.raises(ValidationError):
        GroupUpsert(
            company_id=1,
            code="finance",
            name="Finance",
            channel="email",
            members=[
                {"destination": "finance@example.com"},
                {"destination": "finance@example.com"},
            ],
        )


def test_notification_group_requires_valid_channel():
    with pytest.raises(ValidationError):
        GroupUpsert(
            company_id=1,
            code="finance",
            name="Finance",
            channel="in_app",
            members=[{"destination": "finance@example.com"}],
        )


def test_notification_template_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        TemplateUpsert(
            company_id=1,
            code="payment_due",
            channel="email",
            body_template="Due {{ amount }}",
            smtp_password="should-not-be-accepted",
        )


def test_notification_send_contract_bounds_context_and_idempotency_key():
    payload = SendNotificationRequest(
        company_id=1,
        channel="in_app",
        body="Test message",
        idempotency_key="notification-0001",
        context={"invoice_no": "INV-10"},
    )
    assert payload.idempotency_key == "notification-0001"
    with pytest.raises(ValidationError):
        SendNotificationRequest(
            company_id=1,
            channel="in_app",
            body="Test message",
            idempotency_key="bad key with spaces",
        )
