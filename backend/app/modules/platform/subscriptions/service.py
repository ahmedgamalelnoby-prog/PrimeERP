from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.platform.plans.models import Plan
from app.modules.platform.subscriptions.models import Subscription
from app.modules.platform.subscriptions.repository import subscription_repository
from app.modules.platform.subscriptions.schemas import SubscriptionCreate, SubscriptionUpdate


class SubscriptionService:
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

    def create(self, schema: SubscriptionCreate) -> Subscription:
        plan = self.db.query(Plan).filter(Plan.id == schema.plan_id).first()
        if plan is None:
            raise ValueError("Plan not found")
        now = schema.starts_at or self._now()
        trial_end = schema.trial_ends_at
        if trial_end is None and plan.trial_days > 0:
            trial_end = now + timedelta(days=plan.trial_days)
        period_days = 365 if schema.billing_cycle == "yearly" else 30
        data = schema.model_dump()
        data.update(
            starts_at=now,
            trial_ends_at=trial_end,
            ends_at=schema.ends_at or now + timedelta(days=period_days),
            next_billing_date=schema.ends_at or now + timedelta(days=period_days),
            status="trialing" if trial_end and trial_end > now else "active",
            is_auto_renew=schema.auto_renew,
        )
        data.pop("auto_renew", None)
        instance = self.repository.create(self.db, data)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def activate(self, subscription_id: int) -> Subscription:
        instance = self._get(subscription_id, True)
        now = self._now()
        instance.status = "active"
        instance.trial_ends_at = None
        instance.starts_at = now
        if not instance.ends_at or instance.ends_at <= now:
            instance.ends_at = now + timedelta(days=30)
        instance.next_billing_date = instance.ends_at
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def cancel(self, subscription_id: int, reason: str = "customer_request") -> Subscription:
        instance = self._get(subscription_id, True)
        instance.status = "cancelled"
        instance.cancelled_at = self._now()
        instance.is_auto_renew = False
        instance.notes = f"Cancellation reason: {reason}"
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, subscription_id: int, schema: SubscriptionUpdate) -> Subscription:
        instance = self._get(subscription_id, True)
        data = schema.model_dump(exclude_unset=True)
        if "auto_renew" in data:
            data["is_auto_renew"] = data.pop("auto_renew")
        self.repository.update(self.db, instance, data)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def _expire_if_needed(self, instance: Subscription) -> None:
        now = self._now()
        if instance.status == "trialing" and instance.trial_ends_at and instance.trial_ends_at <= now:
            instance.status = "expired"
            self.db.commit()
        elif instance.status == "active" and instance.ends_at and instance.ends_at <= now:
            instance.status = "expired"
            self.db.commit()

    def is_tenant_access_allowed(self, tenant_id: int) -> bool:
        instance = self.get_active_for_tenant(tenant_id)
        return instance is not None and instance.status in {"trialing", "active", "past_due"}


subscription_service = SubscriptionService
