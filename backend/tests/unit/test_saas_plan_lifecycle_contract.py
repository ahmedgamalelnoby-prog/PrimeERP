from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_saas_lifecycle_resolves_canonical_plan_first():
    source = (ROOT / "app/modules/saas/lifecycle.py").read_text(encoding="utf-8")
    assert "from app.modules.platform.plans.models import Plan" in source
    assert "Plan.status == PlanStatus.ACTIVE.value" in source
    assert "def _canonical_plan_by_code" in source
    assert "def resolve_legacy_plan" in source


def test_trial_registration_uses_canonical_lifecycle_boundary():
    source = (ROOT / "app/modules/saas/service.py").read_text(encoding="utf-8")
    assert "from app.modules.saas.lifecycle import create_trial, resolve_legacy_plan" in source
    assert "subscription, canonical_plan, modules = create_trial(" in source
    assert "db.query(SubscriptionPlan).filter(SubscriptionPlan.code == \"trial\"" not in source


def test_lifecycle_provisions_entitlements_and_expiry_state():
    source = (ROOT / "app/modules/saas/lifecycle.py").read_text(encoding="utf-8")
    assert "def create_trial(" in source
    assert "def convert_trial_to_paid(" in source
    assert "def renew_subscription(" in source
    assert "def cancel_auto_renewal(" in source
    assert "def expire_due_subscriptions(" in source
    assert "_provision_plan_modules" in source
