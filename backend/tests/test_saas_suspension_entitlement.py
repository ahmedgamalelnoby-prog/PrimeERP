from app.modules.saas import entitlements


class _CaptureDB:
    def __init__(self):
        self.statements = []

    def scalar(self, statement):
        self.statements.append(statement)
        return None


def test_active_subscription_query_requires_active_unsuspended_tenant():
    db = _CaptureDB()

    assert entitlements._active_subscription(db, tenant_id=17) is None

    sql = str(db.statements[0]).lower()
    assert "tenants.is_active" in sql
    assert "tenants.status" in sql
    assert "suspended" in sql
