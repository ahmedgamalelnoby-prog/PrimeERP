from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.platform.plans.models import Plan
from app.modules.platform.subscriptions.models import Subscription
from app.modules.platform.subscriptions.repository import subscription_repository
from app.modules.platform.subscriptions.schemas import SubscriptionCreate, SubscriptionUpdate
from app.modules.saas.models import SubscriptionPlan, Tenant


class SubscriptionService:
    """Application boundary for tenant subscription lifecycle and access state."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = subscription_repository

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _get(self, subscription_id: int, for_update: bool = False) -> Subscription:
        instance = self.repository.get_by_id(self.db, subscription_id, for_update)
        if instance is None:
            raise ValueError("Subscription not found")
        return instance

    def list_for_tenant(self, tenant_id: int):
        return self.repository.list_for_tenant(self.db, tenant_id)

    def get_active_for_tenant(self, tenant_id: int):
        instance = self.repository.get_active_for_tenant(self.db, tenant_id)
        if instance is not None:
            self._expire_if_needed(instance)
        return instance

    def _resolve_plan(self, plan_id: int) -> Plan:
        plan = self.db.query(Plan).filter(Plan.id == plan_id).first()
        if plan is not None:
            return plan

        # Compatibility path for tenants created before the canonical plans module.
        legacy = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if legacy is None:
            raise ValueError("Plan not found")

        plan = Plan(
            id=legacy.id,
            code=legacy.code,
            version=1,
            name=legacy.name_en,
            name_ar=legacy.name_ar,
            display_name=legacy.name_en,
            description=legacy.description_en,
            monthly_price=legacy.monthly_price,
            yearly_price=legacy.yearly_price,
            currency=legacy.currency_code,
            billing_cycle="monthly",
            trial_days=legacy.trial_days,
            grace_period_days=7,
            is_public=legacy.is_public,
            is_free=legacy.monthly_price == 0 and legacy.yearly_price == 0,
            status="active" if legacy.is_active else "inactive",
            plan_type="standard",
            sort_order=legacy.display_order,
        )
        self.db.add(plan)
        self.db.flush()
        return plan

    def _ensure_legacy_subscription_plan(self, plan: Plan) -> None:
        """Keep the legacy FK target synchronized until the physical table is migrated."""
        legacy = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan.id).first()
        if legacy is not None:
            if legacy.code != plan.code:
                raise ValueError("Plan identifier is already used by a different legacy plan")
            return

        self.db.add(
            SubscriptionPlan(
                id=plan.id,
                name_ar=plan.name_ar or plan.name,
                name_en=plan.name,
                code=plan.code,
                description_en=plan.description,
                monthly_price=plan.monthly_price,
                yearly_price=plan.yearly_price,
                currency_code=plan.currency,
                trial_days=plan.trial_days,
                is_public=plan.is_public,
                is_active=plan.status == "active",
                display_order=plan.sort_order,
            )
        )
        self.db.flush()

    def create(self, schema: SubscriptionCreate) -> Subscription:
        plan = self._resolve_plan(schema.plan_id)
        now = schema.starts_at or self._now()
        trial_end = schema.trial_ends_at
        if trial_end is None and plan.trial_days > 0:
            trial_end = now + timedelta(days=plan.trial_days)

        period_days = 365 if schema.billing_cycle == "yearly" else 30
        ends_at = schema.ends_at or now + timedelta(days=period_days)
        conflict = self.repository.get_conflicting_for_tenant(
            self.db,
            schema.tenant_id,
            starts_at=now,
            ends_at=ends_at,
        )
        if conflict is not None:
            raise ValueError("Tenant already has an overlapping active subscription")

        self._ensure_legacy_subscription_plan(plan)
        status = "trialing" if trial_end and trial_end > now else "active"
        data = schema.model_dump()
        data.update(
            starts_at=now,
            trial_ends_at=trial_end,
            ends_at=ends_at,
            next_billing_date=ends_at,
            status=status,
            is_auto_renew=schema.auto_renew,
        )
        data.pop("auto_renew", None)
        instance = self.repository.create(self.db, data)
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def activate(self, subscription_id: int) -> Subscription:
        instance = self._get(subscription_id, True)
        now = self._now()
        period_days = 365 if instance.billing_cycle == "yearly" else 30
        instance.status = "active"
        instance.trial_ends_at = None
        instance.starts_at = now
        instance.ends_at = now + timedelta(days=period_days)
        instance.next_billing_date = instance.ends_at
        instance.cancelled_at = None
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def cancel(self, subscription_id: int, reason: str = "customer_request") -> Subscription:
        instance = self._get(subscription_id, True)
        instance.status = "cancelled"
        instance.cancelled_at = self._now()
        instance.is_auto_renew = False
        instance.notes = f"Cancellation reason: {reason}"
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, subscription_id: int, schema: SubscriptionUpdate) -> Subscription:
        instance = self._get(subscription_id, True)
        data = schema.model_dump(exclude_unset=True)
        if "auto_renew" in data:
            data["is_auto_renew"] = data.pop("auto_renew")
        self.repository.update(self.db, instance, data)
        self._sync_tenant_state(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def _sync_tenant_state(self, instance: Subscription) -> None:
        tenant = self.db.query(Tenant).filter(Tenant.id == instance.tenant_id).with_for_update().first()
        if tenant is None:
            raise ValueError("Tenant not found")

        allowed = instance.status in {"trialing", "active", "past_due"}
        tenant.is_active = allowed
        tenant.is_trial = instance.status == "trialing"
        tenant.status = "trial" if instance.status == "trialing" else ("active" if allowed else "expired")
        tenant.trial_ends_at = instance.trial_ends_at if instance.status == "trialing" else None

    def _expire_if_needed(self, instance: Subscription) -> None:
        now = self._now()
        changed = False
        if instance.status == "trialing" and instance.trial_ends_at and instance.trial_ends_at <= now:
            instance.status = "expired"
            changed = True
        elif instance.status == "active" and instance.ends_at and instance.ends_at <= now:
            instance.status = "expired"
            changed = True

        if changed:
            self._sync_tenant_state(instance)
            self.db.commit()

    def is_tenant_access_allowed(self, tenant_id: int) -> bool:
        instance = self.get_active_for_tenant(tenant_id)
        return instance is not None and instance.status in {"trialing", "active", "past_due"}


subscription_service = SubscriptionService
