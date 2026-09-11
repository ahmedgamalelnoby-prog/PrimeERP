from types import SimpleNamespace

from app.modules.identity.api.router import get_me


def test_platform_admin_me_does_not_require_subscription(monkeypatch):
    user = SimpleNamespace(
        id=1,
        tenant_id=10,
        tenant=SimpleNamespace(
            id=10,
            slug="legacy-tenant",
            name="Legacy Tenant",
            status="active",
        ),
        username="platform-admin",
        email="admin@example.test",
        full_name="Platform Admin",
        role_id=None,
        is_active=True,
        is_superuser=True,
        is_platform_admin=True,
        preferred_language="en",
    )

    def fail_if_subscription_is_checked(*args, **kwargs):
        raise AssertionError("platform admin must not require a subscription")

    monkeypatch.setattr(
        "app.modules.identity.api.router.authentication_service._get_valid_subscription",
        fail_if_subscription_is_checked,
    )

    result = get_me(current_user=user, db=object())

    assert result["is_platform_admin"] is True
    assert result["subscription_status"] is None
    assert result["enabled_modules"] == []
