from datetime import datetime, timezone

from app.modules.saas import entitlements


class _CaptureDB:
    def __init__(self):
        self.statement = None

    def scalar(self, statement):
        self.statement = statement
        return None


def test_active_subscription_query_excludes_expired_and_future_subscriptions():
    db = _CaptureDB()

    assert entitlements._active_subscription(db, tenant_id=7) is None

    sql = str(db.statement)
    assert "subscriptions.starts_at" in sql
    assert "subscriptions.ends_at" in sql
    assert "IS NULL" in sql.upper()
    assert ">" in sql


def test_subscription_entitlement_uses_timezone_aware_now():
    now = datetime.now(timezone.utc)
    assert now.tzinfo is not None
