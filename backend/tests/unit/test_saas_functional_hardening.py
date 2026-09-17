from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_entitlements_keep_paid_tenants_in_grace_access():
    source = (ROOT / "app/modules/saas/entitlements.py").read_text(encoding="utf-8")
    assert 'ACTIVE_SUBSCRIPTION_STATUSES = ("trialing", "active", "past_due", "grace")' in source


def test_trial_expiry_does_not_receive_paid_grace_period():
    source = (ROOT / "app/modules/saas/lifecycle.py").read_text(encoding="utf-8")
    assert 'if subscription.status == "trialing":' in source
    assert 'subscription.status = "expired"' in source


def test_grace_reactivation_preserves_grace_state():
    source = (ROOT / "app/modules/saas/lifecycle.py").read_text(encoding="utf-8")
    assert '"grace" if subscription.status == "grace"' in source


def test_custom_product_limit_is_a_first_class_subscription_override():
    model = (ROOT / "app/modules/saas/models.py").read_text(encoding="utf-8")
    schema = (ROOT / "app/modules/platform/subscriptions/schemas.py").read_text(encoding="utf-8")
    assert "custom_max_products = Column(Integer, nullable=True)" in model
    assert "custom_max_products: Optional[int]" in schema


def test_platform_subscription_changes_reconcile_plan_modules():
    source = (ROOT / "app/modules/platform/subscriptions/service.py").read_text(encoding="utf-8")
    assert "def _sync_modules" in source
    assert "self._sync_modules(instance)" in source
    assert "if plan_changed:" in source


def test_identity_covers_all_release_level_platform_modules():
    source = (ROOT / "app/core/module_engine/identity.py").read_text(encoding="utf-8")
    for code in ("uom", "audit", "roles", "reports", "commissions", "commerce", "transactions", "enterprise", "legal", "jurisdiction", "catalog"):
        assert f'"{code}":' in source
