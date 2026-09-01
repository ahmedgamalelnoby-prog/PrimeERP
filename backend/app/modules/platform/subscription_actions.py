from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


def activate_subscription(db: Session, subscription_id: int, actor_id: int, duration_days: int | None = None) -> dict:
    row = db.execute(text("""
        SELECT s.id, s.tenant_id, s.status, s.billing_cycle
        FROM subscriptions s WHERE s.id=:id
    """), {"id": subscription_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Subscription not found")

    now = datetime.now(timezone.utc)
    days = duration_days or (365 if row["billing_cycle"] == "yearly" else 30)
    end = now + timedelta(days=days)

    db.execute(text("""
        UPDATE subscriptions SET status='active', starts_at=:starts, ends_at=:ends,
          trial_ends_at=NULL, next_billing_date=:ends, cancelled_at=NULL, updated_at=:now
        WHERE id=:id
    """), {"starts": now, "ends": end, "now": now, "id": subscription_id})
    db.execute(text("""
        UPDATE tenants SET status='active', is_trial=false, is_active=true,
          suspended_at=NULL, suspension_reason=NULL, updated_at=:now
        WHERE id=:tenant_id
    """), {"now": now, "tenant_id": row["tenant_id"]})

    # Entitlements come from the selected plan. Existing tenant-specific modules
    # are preserved when they are explicitly present; plan modules are restored.
    db.execute(text("""
        INSERT INTO tenant_modules (tenant_id, module_id, is_enabled, starts_at, ends_at)
        SELECT :tenant_id, pm.module_id, true, :starts, :ends
        FROM plan_modules pm
        JOIN subscriptions s ON s.plan_id=pm.plan_id
        WHERE s.id=:subscription_id AND pm.is_enabled=true
        ON CONFLICT (tenant_id, module_id) DO UPDATE SET
          is_enabled=true, starts_at=:starts, ends_at=:ends
    """), {"tenant_id": row["tenant_id"], "subscription_id": subscription_id, "starts": now, "ends": end})

    db.execute(text("""
        INSERT INTO subscription_events
        (subscription_id, tenant_id, event_type, from_status, to_status, actor_user_id, metadata_json)
        VALUES (:sid,:tid,'activated',:old,'active',:actor,:meta)
    """), {"sid": subscription_id, "tid": row["tenant_id"], "old": row["status"], "actor": actor_id, "meta": json.dumps({"duration_days": days})})
    db.commit()
    return {"subscription_id": subscription_id, "status": "active", "starts_at": now, "ends_at": end}
