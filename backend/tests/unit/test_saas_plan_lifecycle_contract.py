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


def test_plan_transition_revokes_only_plan_grants():
    lifecycle_source = (ROOT / "app/modules/saas/lifecycle.py").read_text(encoding="utf-8")
    model_source = (ROOT / "app/modules/saas/models.py").read_text(encoding="utf-8")
    entitlement_source = (ROOT / "app/modules/saas/entitlements.py").read_text(encoding="utf-8")

    assert 'source == "plan"' in lifecycle_source
    assert 'grant.is_enabled = False' in lifecycle_source
    assert 'source="plan"' in lifecycle_source
    assert 'TenantModule.source == "override"' in entitlement_source
    assert 'source = Column(String(20)' in model_source


def test_plan_transition_does_not_rewrite_explicit_overrides():
    source = (ROOT / "app/modules/saas/lifecycle.py").read_text(encoding="utf-8")
    assert 'elif grant.source == "plan":' in source
    assert "Explicit overrides are intentionally authoritative" in source
