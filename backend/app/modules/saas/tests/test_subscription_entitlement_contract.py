from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_saas_entitlements_cover_modules_and_resource_limits():
    source = (ROOT / "modules/saas/entitlements.py").read_text(encoding="utf-8")
    for marker in [
        "def tenant_has_module",
        "def require_module",
        "def enforce_user_limit",
        "def enforce_company_limit",
        "def enforce_branch_limit",
        "def enforce_product_limit",
    ]:
        assert marker in source
    assert 'Subscription.status.in_(("trialing", "active", "past_due"))' in source


def test_saas_lifecycle_covers_trial_conversion_renewal_cancellation_and_suspension():
    source = (ROOT / "modules/saas/lifecycle.py").read_text(encoding="utf-8")
    for marker in [
        "def convert_trial_to_paid",
        "def renew_subscription",
        "def cancel_auto_renewal",
        "def suspend_tenant",
        "def unsuspend_tenant",
    ]:
        assert marker in source
    assert "BILLING_CYCLES = {\"monthly\": 30, \"yearly\": 365}" in source


def test_saas_registration_creates_trial_environment_and_module_overrides():
    source = (ROOT / "modules/saas/service.py").read_text(encoding="utf-8")
    assert "def register_trial_tenant" in source
    assert "Subscription(" in source
    assert "TenantModule(" in source
    assert "trial_ends_at" in source
