from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session


ACTIVE_STATUSES = {"trialing", "active", "grace"}
BLOCKED_STATUSES = {"expired", "suspended", "cancelled"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def require_platform_admin(user) -> None:
    if not getattr(user, "is_platform_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin access required")


def refresh_expired_subscriptions(db: Session) -> int:
    now = _now()
    rows = db.execute(
        text("""
            SELECT s.id, s.tenant_id, s.status, s.ends_at, p.grace_period_days
            FROM subscriptions s
            JOIN subscription_plans p ON p.id = s.plan_id
            WHERE s.status IN ('trialing', 'active', 'grace')
              AND s.ends_at IS NOT NULL
              AND s.ends_at < :now
        """),
        {"now": now},
    ).mappings().all()

    changed = 0
    for row in rows:
        old = row["status"]
        grace_days = int(row["grace_period_days"] or 0)
        grace_end = row["ends_at"] + timedelta(days=grace_days)
        if old != "grace" and grace_days > 0 and now < grace_end:
            new_status = "grace"
        else:
            new_status = "expired"

        db.execute(
            text("UPDATE subscriptions SET status=:status, updated_at=:now WHERE id=:id"),
            {"status": new_status, "now": now, "id": row["id"]},
        )
        db.execute(
            text("UPDATE tenants SET status=:status, is_trial=false, is_active=:active, updated_at=:now WHERE id=:tenant_id"),
            {"status": new_status, "active": new_status != "suspended", "now": now, "tenant_id": row["tenant_id"]},
        )
        db.execute(
            text("""
                INSERT INTO subscription_events
                (subscription_id, tenant_id, event_type, from_status, to_status, metadata_json)
                VALUES (:sid, :tid, 'status_changed', :old, :new, :meta)
            """),
            {"sid": row["id"], "tid": row["tenant_id"], "old": old, "new": new_status, "meta": json.dumps({"reason": "automatic_expiration"})},
        )
        if new_status == "expired":
            db.execute(
                text("UPDATE tenant_modules SET is_enabled=false, ends_at=:now WHERE tenant_id=:tenant_id"),
                {"now": now, "tenant_id": row["tenant_id"]},
            )
        changed += 1

    if changed:
        db.commit()
    return changed


def platform_dashboard(db: Session) -> dict:
    refresh_expired_subscriptions(db)
    counts = db.execute(text("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status='trial') AS trial,
            COUNT(*) FILTER (WHERE status='active') AS active,
            COUNT(*) FILTER (WHERE status='expired') AS expired,
            COUNT(*) FILTER (WHERE status='suspended') AS suspended
        FROM tenants
    """)).mappings().one()
    pending = db.execute(text("SELECT COUNT(*) AS count FROM payment_requests WHERE status='pending'")).scalar_one()
    revenue = db.execute(text("SELECT COALESCE(SUM(total_amount),0) FROM invoices WHERE status='paid'")).scalar_one()
    return {**dict(counts), "pending_payments": pending, "paid_revenue": revenue}


def public_catalog(db: Session) -> dict:
    plans = db.execute(text("""
        SELECT id, code, name_ar, name_en, description_ar, description_en,
               monthly_price, yearly_price, currency_code, trial_days,
               max_users, max_companies, max_branches, is_public, is_active
        FROM subscription_plans
        WHERE is_public=true AND is_active=true
        ORDER BY display_order, id
    """)).mappings().all()
    modules = db.execute(text("""
        SELECT sm.id, sm.code, sm.name_ar, sm.name_en, sm.description_ar,
               sm.description_en, sm.is_core, sm.is_active,
               mp.currency_code, mp.monthly_base_price, mp.yearly_base_price,
               mp.monthly_user_price, mp.yearly_user_price
        FROM system_modules sm
        LEFT JOIN module_prices mp ON mp.module_id=sm.id AND mp.is_active=true
        WHERE sm.is_active=true
        ORDER BY sm.display_order, sm.id
    """)).mappings().all()
    return {"plans": [dict(x) for x in plans], "modules": [dict(x) for x in modules]}


def list_trials(db: Session) -> list[dict]:
    refresh_expired_subscriptions(db)
    rows = db.execute(text("""
        SELECT t.id, t.name, t.slug, t.owner_name, t.email, t.phone,
               t.status, t.trial_started_at, t.trial_ends_at,
               s.id AS subscription_id, sp.code AS plan_code
        FROM tenants t
        LEFT JOIN subscriptions s ON s.tenant_id=t.id
        LEFT JOIN subscription_plans sp ON sp.id=s.plan_id
        WHERE t.status IN ('trial', 'trialing') OR t.is_trial=true
        ORDER BY t.created_at DESC
    """)).mappings().all()
    return [dict(x) for x in rows]


def list_payment_requests(db: Session, status_filter: str | None = None) -> list[dict]:
    query = """
        SELECT pr.*, t.name AS tenant_name, i.invoice_number
        FROM payment_requests pr
        JOIN tenants t ON t.id=pr.tenant_id
        LEFT JOIN invoices i ON i.id=pr.invoice_id
    """
    params = {}
    if status_filter:
        query += " WHERE pr.status=:status"
        params["status"] = status_filter
    query += " ORDER BY pr.created_at DESC"
    return [dict(x) for x in db.execute(text(query), params).mappings().all()]


def activate_subscription(db: Session, subscription_id: int, actor_id: int, duration_days: int | None = None) -> dict:
    row = db.execute(text("""
        SELECT s.*, p.trial_days, p.max_users, p.grace_period_days
        FROM subscriptions s JOIN subscription_plans p ON p.id=s.plan_id
        WHERE s.id=:id
    """), {"id": subscription_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Subscription not found")

    now = _now()
    days = duration_days or (365 if row["billing_cycle"] == "yearly" else 30)
    end = now + timedelta(days=days)
    db.execute(text("""
        UPDATE subscriptions
        SET status='active', starts_at=:starts, ends_at=:ends, trial_ends_at=NULL,
            next_billing_date=:ends, updated_at=:now
        WHERE id=:id
    """), {"starts": now, "ends": end, "now": now, "id": subscription_id})
    db.execute(text("""
        UPDATE tenants SET status='active', is_trial=false, is_active=true, updated_at=:now
        WHERE id=:tenant_id
    """), {"now": now, "tenant_id": row["tenant_id"]})
    db.execute(text("""
        INSERT INTO subscription_events
        (subscription_id, tenant_id, event_type, from_status, to_status, actor_user_id, metadata_json)
        VALUES (:sid,:tid,'activated',:old,'active',:actor,:meta)
    """), {"sid": subscription_id, "tid": row["tenant_id"], "old": row["status"], "actor": actor_id, "meta": json.dumps({"duration_days": days})})
    db.commit()
    return {"subscription_id": subscription_id, "status": "active", "starts_at": now, "ends_at": end}


def approve_payment(db: Session, payment_id: int, actor_id: int, duration_days: int | None = None) -> dict:
    payment = db.execute(text("SELECT * FROM payment_requests WHERE id=:id"), {"id": payment_id}).mappings().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment request not found")
    if payment["status"] != "pending":
        raise HTTPException(status_code=409, detail="Payment request is already reviewed")

    now = _now()
    db.execute(text("""
        UPDATE payment_requests
        SET status='approved', reviewed_by=:actor, reviewed_at=:now, updated_at=:now
        WHERE id=:id
    """), {"actor": actor_id, "now": now, "id": payment_id})
    if payment["invoice_id"]:
        db.execute(text("UPDATE invoices SET status='paid', paid_at=:now WHERE id=:id"), {"now": now, "id": payment["invoice_id"]})
    result = activate_subscription(db, int(payment["subscription_id"]), actor_id, duration_days) if payment["subscription_id"] else {"status": "approved"}
    return {"payment_id": payment_id, **result}


def reject_payment(db: Session, payment_id: int, actor_id: int, note: str | None = None) -> dict:
    now = _now()
    result = db.execute(text("""
        UPDATE payment_requests
        SET status='rejected', reviewed_by=:actor, reviewed_at=:now, review_note=:note, updated_at=:now
        WHERE id=:id AND status='pending'
        RETURNING id
    """), {"actor": actor_id, "now": now, "note": note, "id": payment_id}).first()
    if not result:
        raise HTTPException(status_code=409, detail="Payment request is not pending")
    db.commit()
    return {"payment_id": payment_id, "status": "rejected"}
