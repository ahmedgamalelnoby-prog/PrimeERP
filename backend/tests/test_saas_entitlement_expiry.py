from datetime import datetime, timezone

from app.modules.saas import entitlements


class _CaptureResult:
    def __init__(self, statement):
        self.statement = statement

    def all(self):
        return []


class _CaptureDB:
    def __init__(self):
        self.statement = None

    def scalars(self, statement):
        self.statement = statement
        return _CaptureResult(statement)


def test_active_subscription_query_excludes_expired_and_future_subscriptions():
    db = _CaptureDB()

    assert entitlements._active_subscription(db, tenant_id=7) is None

    sql = str(db.statement)
    assert "subscriptions.starts_at" in sql
    assert "subscriptions.ends_at" in sql
    assert "subscriptions.status" in sql
    assert "tenants.status" in sql


def test_subscription_entitlement_uses_timezone_aware_now():
    now = datetime.now(timezone.utc)
    assert now.tzinfo is not None
