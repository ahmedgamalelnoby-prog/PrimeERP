from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.platform.subscriptions.models import Subscription


ACTIVE_STATUSES = ("trialing", "active", "past_due")


class SubscriptionRepository:
    def get_by_id(self, db: Session, subscription_id: int, for_update: bool = False):
        query = db.query(Subscription).filter(Subscription.id == subscription_id)
        if for_update:
            query = query.with_for_update()
        return query.first()

    def get_active_for_tenant(self, db: Session, tenant_id: int):
        return (
            db.query(Subscription)
            .filter(
                Subscription.tenant_id == tenant_id,
                Subscription.status.in_(ACTIVE_STATUSES),
            )
            .order_by(Subscription.id.desc())
            .first()
        )

    def get_conflicting_for_tenant(
        self,
        db: Session,
        tenant_id: int,
        starts_at: datetime,
        ends_at: datetime | None,
        exclude_id: int | None = None,
    ):
        query = db.query(Subscription).filter(
            Subscription.tenant_id == tenant_id,
            Subscription.status.in_(ACTIVE_STATUSES),
            Subscription.starts_at < (ends_at or datetime.max),
            (Subscription.ends_at.is_(None) | (Subscription.ends_at > starts_at)),
        )
        if exclude_id is not None:
            query = query.filter(Subscription.id != exclude_id)
        return query.order_by(Subscription.id.desc()).first()

    def list_for_tenant(self, db: Session, tenant_id: int):
        return (
            db.query(Subscription)
            .filter(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.id.desc())
            .all()
        )

    def create(self, db: Session, data: dict) -> Subscription:
        instance = Subscription(**data)
        db.add(instance)
        db.flush()
        return instance

    def update(self, db: Session, instance: Subscription, data: dict) -> Subscription:
        for key, value in data.items():
            setattr(instance, key, value)
        db.flush()
        return instance


subscription_repository = SubscriptionRepository()
