from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.platform.plans.models import Plan
from app.modules.platform.subscriptions.models import Subscription
from app.modules.platform.subscriptions.repository import subscription_repository
from app.modules.platform.subscriptions.schemas import SubscriptionConvertToPaid, SubscriptionCreate, SubscriptionUpdate
from app.modules.saas.models import SubscriptionPlan, Tenant


class SubscriptionService:
    """Application boundary for tenant subscription lifecycle and access state."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = subscription_repository

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _period_days(billing_cycle: str) -> int:
        return {"monthly": 30, "quarterly": 90, "semi_annual": 182, "yearly": 365}.get(billing_cycle, 30)

    @classmethod
    def _subscription_is_current(cls, instance: Subscription) -> bool:
        if instance.status not in {"trialing", "active", "past_due"}:
            return False
        now = cls._now()
        starts_at = getattr(instance, "starts_at", None)
        ends_at = getattr(instance, "ends_at", None)
        if starts_at is not None:
            if starts_at.tzinfo is None:
                starts_at = starts_at.replace(tzinfo=timezone.utc)
            if starts_at > now:
                return False
        if ends_at is not None:
            if ends_at.tzinfo is None:
                ends_at = ends_at.replace(tzinfo=timezone.utc)
            if ends_at <= now:
                return False
        trial_ends_at = getattr(instance, "trial_ends_at", None)
        if instance.status == "trialing" and trial_ends_at is not None:
            if trial_ends_at.tzinfo is None:
                trial_ends_at = trial_ends_at.replace(tzinfo=timezone.utc)
            if trial_ends_at <= now:
                return False
        return True

    def _get(self, subscription_id: int, for_update: bool = False) -> Subscription:
        instance = self.repository.get_by_id(self.db, subscription_id, for_update)
        if instance is None:
            raise ValueError("Subscription not found")
        return instance

    def _locked_tenant(self, tenant_id: int) -> Tenant:
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).with_for_update().first()
        if tenant is None:
            raise ValueError("Tenant not found")
        return tenant

    def list_for_tenant(self, tenant_id: int):
        return self.repository.list_for_tenant(self.db, tenant_id)

    def get_active_for_tenant(self, tenant_id: int):
        instance = self.repository.get_latest_for_tenant(self.db, tenant_id)
        if instance is None:
            return None
        self._expire_if_needed(instance)
        if not self._subscription_is_current(instance):
            self._reconcile_tenant_state_if_needed(instance)
            return None
        self._reconcile_tenant_state_if_needed(instance)
        return instance

    def is_tenant_access_allowed(self, tenant_id: int) -> bool:
        return self.get_active_for_tenant(tenant_id) is not None

    def _resolve_plan(self, plan_id: int) -> Plan:
        plan = self.db.query(Plan).filter(Plan.id == plan_id).first()
        if plan is not None:
            return plan
        legacy = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if legacy is None:
            raise ValueError("Plan not found")
        plan = Plan(
            id=legacy.id, code=legacy.code, version=1, name=legacy.name_en, name_ar=legacy.name_ar,
            display_name=legacy.name_en, description=legacy.description_en, monthly_price=legacy.monthly_price,
            yearly_price=legacy.yearly_price, currency=legacy.currency_code, billing_cycle="monthly",
            trial_days=legacy.trial_days, grace_period_days=7, max_users=legacy.max_users,
            max_companies=legacy.max_companies, max_branches=legacy.max_branches, max_products=legacy.max_products,
            max_integrations=legacy.max_integrations, storage_limit_mb=legacy.storage_limit_mb,
            is_public=legacy.is_public, is_free=legacy.monthly_price == 0 and legacy.yearly_price == 0,
            status="active" if legacy.is_active else "inactive", plan_type="standard", sort_order=legacy.display_order,
        )
        self.db.add(plan)
        self.db.flush()
        return plan

    def _grace_period_days(self, plan_id: int) -> int:
        plan = self.db.query(Plan).filter(Plan.id == plan_id).first()
        if plan is not None:
            return max(int(plan.grace_period_days or 0), 0)
        legacy = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        return 7 if legacy is not None else 0

    def _ensure_legacy_subscription_plan(self, plan: Plan) -> None:
        legacy = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan.id).first()
        if legacy is not None:
            if legacy.code != plan.code:
                raise ValueError("Plan identifier is already used by a different legacy plan")
            legacy.name_ar = plan.name_ar or plan.name
            legacy.name_en = plan.name
            legacy.description_en = plan.description
            legacy.monthly_price = plan.monthly_price
            legacy.yearly_price = plan.yearly_price
            legacy.currency_code = plan.currency
            legacy.trial_days = plan.trial_days
            legacy.is_public = plan.is_public
            legacy.is_active = plan.status == "active"
            legacy.display_order = plan.sort_order
            legacy.max_users = plan.max_users
            legacy.max_companies = plan.max_companies
            legacy.max_branches = plan.max_branches
            legacy.max_products = plan.max_products
            legacy.max_integrations = plan.max_integrations
            legacy.storage_limit_mb = plan.storage_limit_mb
            return
        self.db.add(SubscriptionPlan(
            id=plan.id, name_ar=plan.name_ar or plan.name, name_en=plan.name, code=plan.code,
            description_en=plan.description, monthly_price=plan.monthly_price, yearly_price=plan.yearly_price,
            currency_code=plan.currency, trial_days=plan.trial_days, is_public=plan.is_public,
            is_active=plan.status == "active", display_order=plan.sort_order, max_users=plan.max_users,
            max_companies=plan.max_companies, max_branches=plan.max_branches, max_products=plan.max_products,
            max_integrations=plan.max_integrations, storage_limit_mb=plan.storage_limit_mb,
        ))
        self.db.flush()

    def create(self, schema: SubscriptionCreate) -> Subscription:
        plan = self._resolve_plan(schema.plan_id)
        if plan.status != "active":
            raise ValueError("Only active plans can be subscribed to")
        self._locked_tenant(schema.tenant_id)
        now = schema.starts_at or self._now()
        trial_end = schema.trial_ends_at
        if trial_end is None and plan.trial_days > 0:
            trial_end = now + timedelta(days=plan.trial_days)
        if trial_end is not None and trial_end <= now:
            raise ValueError("Trial end date must be after its start date")
        ends_at = schema.ends_at or now + timedelta(days=self._period_days(schema.billing_cycle))
        if ends_at <= now:
            raise ValueError("Subscription end date must be after its start date")
        conflict = self.repository.get_conflicting_for_tenant(self.db, schema.tenant_id, starts_at=now, ends_at=ends_at)
        if conflict is not None:
            raise ValueError("Tenant already has an overlapping active subscription")
        self._ensure_legacy_subscription_plan(plan)
        subscription_status = "trialing" if trial_end and trial_end > now else "active"
        data = schema.model_dump()
        data.update(starts_at=now, trial_ends_at=trial_end, ends_at=ends_at, next_billing_date=ends_at if schema.auto_renew else None, status=subscription_status, is_auto_renew=schema.auto_renew)
        data.pop("auto_renew", None)
        instance = self.repository.create(self.db, data)
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def activate(self, subscription_id: int) -> Subscription:
        instance = self._get(subscription_id, True)
        if instance.status not in {"trialing", "past_due"}:
            raise ValueError("Only trialing or past_due subscriptions can be activated")
        tenant = self._locked_tenant(instance.tenant_id)
        if tenant.status == "suspended" or not tenant.is_active:
            raise ValueError("Tenant requires explicit reactivation before subscription activation")
        now = self._now()
        instance.status = "active"
        instance.trial_ends_at = None
        instance.starts_at = now
        instance.ends_at = now + timedelta(days=self._period_days(instance.billing_cycle))
        instance.next_billing_date = instance.ends_at if instance.is_auto_renew else None
        instance.cancelled_at = None
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def convert_to_paid(self, subscription_id: int, schema: SubscriptionConvertToPaid) -> Subscription:
        instance = self._get(subscription_id, True)
        if instance.status not in {"trialing", "past_due"}:
            raise ValueError("Only trialing or past_due subscriptions can be converted to paid")
        tenant = self._locked_tenant(instance.tenant_id)
        if tenant.status == "suspended" or not tenant.is_active:
            raise ValueError("Tenant requires explicit reactivation before paid conversion")
        now = schema.starts_at or self._now()
        billing_cycle = schema.billing_cycle or instance.billing_cycle
        if schema.plan_id is not None:
            plan = self._resolve_plan(schema.plan_id)
            if plan.status != "active":
                raise ValueError("Only active plans can be used for paid conversion")
            self._ensure_legacy_subscription_plan(plan)
            instance.plan_id = plan.id
        instance.billing_cycle = billing_cycle
        instance.status = "active"
        instance.trial_ends_at = None
        instance.cancelled_at = None
        instance.starts_at = now
        instance.ends_at = schema.ends_at or now + timedelta(days=self._period_days(billing_cycle))
        if instance.ends_at <= now:
            raise ValueError("Paid subscription end date must be after its start date")
        if schema.auto_renew is not None:
            instance.is_auto_renew = schema.auto_renew
        instance.next_billing_date = instance.ends_at if instance.is_auto_renew else None
        if schema.notes is not None:
            instance.notes = schema.notes
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def cancel(self, subscription_id: int, reason: str = "customer_request") -> Subscription:
        instance = self._get(subscription_id, True)
        instance.status = "cancelled"
        instance.cancelled_at = self._now()
        instance.is_auto_renew = False
        instance.next_billing_date = None
        instance.notes = f"Cancellation reason: {reason}"
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, subscription_id: int, schema: SubscriptionUpdate) -> Subscription:
        instance = self._get(subscription_id, True)
        data = schema.model_dump(exclude_unset=True)
        if "plan_id" in data:
            plan = self._resolve_plan(data["plan_id"])
            if plan.status != "active":
                raise ValueError("Only active plans can be assigned to a subscription")
            self._ensure_legacy_subscription_plan(plan)
        auto_renew = data.pop("auto_renew", None) if "auto_renew" in data else None
        if auto_renew is not None:
            data["is_auto_renew"] = auto_renew
        if "ends_at" in data:
            if data["ends_at"] is not None and data["ends_at"] <= instance.starts_at:
                raise ValueError("Subscription end date must be after its start date")
            if data["ends_at"] is None:
                data["next_billing_date"] = None
            elif auto_renew is not None:
                data["next_billing_date"] = data["ends_at"] if auto_renew else None
        elif auto_renew is not None:
            data["next_billing_date"] = instance.ends_at if auto_renew else None
        self.repository.update(self.db, instance, data)
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def _sync_tenant_state(self, instance: Subscription) -> None:
        tenant = self.db.query(Tenant).filter(Tenant.id == instance.tenant_id).with_for_update().first()
        if tenant is None:
            raise ValueError("Tenant not found")
        allowed = self._subscription_is_current(instance)
        if tenant.status == "suspended":
            tenant.is_active = False
            tenant.is_trial = instance.status == "trialing" and allowed
            tenant.trial_ends_at = instance.trial_ends_at if instance.status == "trialing" and allowed else None
            return
        tenant.is_active = allowed
        tenant.is_trial = instance.status == "trialing" and allowed
        tenant.status = "trial" if instance.status == "trialing" and allowed else ("active" if allowed else "expired")
        tenant.trial_ends_at = instance.trial_ends_at if instance.status == "trialing" and allowed else None

    def _reconcile_tenant_state_if_needed(self, instance: Subscription) -> None:
        tenant = self.db.query(Tenant).filter(Tenant.id == instance.tenant_id).first()
        if tenant is None:
            raise ValueError("Tenant not found")
        if tenant.status == "suspended":
            if tenant.is_active:
                tenant.is_active = False
                self.db.commit()
            return
        allowed = self._subscription_is_current(instance)
        expected_status = "trial" if instance.status == "trialing" and allowed else ("active" if allowed else "expired")
        expected_trial_end = instance.trial_ends_at if instance.status == "trialing" and allowed else None
        stale = (
            tenant.is_active != allowed or tenant.is_trial != (instance.status == "trialing" and allowed)
            or tenant.status != expected_status or tenant.trial_ends_at != expected_trial_end
            or tenant.suspended_at is not None or tenant.suspension_reason is not None
        )
        if stale:
            self._sync_tenant_state(instance)
            tenant.suspended_at = None
            tenant.suspension_reason = None
            self.db.commit()

    def _expire_if_needed(self, instance: Subscription) -> None:
        now = self._now()
        changed = False
        if instance.status == "trialing" and instance.trial_ends_at and instance.trial_ends_at <= now:
            instance.status = "expired"
            changed = True
        elif instance.status == "active" and instance.ends_at and instance.ends_at <= now:
            instance.status = "expired"
            changed = True
        elif instance.status == "past_due" and instance.ends_at:
            grace_days = self._grace_period_days(instance.plan_id)
            if instance.ends_at + timedelta(days=grace_days) <= now:
                instance.status = "expired"
                changed = True
        if changed:
            self._sync_tenant_state(instance)
            self.db.commit()


def subscription_service(db: Session) -> SubscriptionService:
    return SubscriptionService(db)
