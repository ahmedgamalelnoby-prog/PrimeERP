from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.platform.subscription_actions import activate_subscription


def approve_payment(db: Session, payment_id: int, actor_id: int, duration_days: int | None = None) -> dict:
    payment = db.execute(text("SELECT * FROM payment_requests WHERE id=:id"), {"id": payment_id}).mappings().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment request not found")
    if payment["status"] != "pending":
        raise HTTPException(status_code=409, detail="Payment request is already reviewed")
    now = datetime.now(timezone.utc)
    db.execute(text("""
        UPDATE payment_requests SET status='approved', reviewed_by=:actor,
        reviewed_at=:now, updated_at=:now WHERE id=:id
    """), {"actor": actor_id, "now": now, "id": payment_id})
    if payment["invoice_id"]:
        db.execute(text("UPDATE invoices SET status='paid', paid_at=:now WHERE id=:id"), {"now": now, "id": payment["invoice_id"]})
    db.commit()
    if payment["subscription_id"]:
        result = activate_subscription(db, int(payment["subscription_id"]), actor_id, duration_days)
    else:
        result = {"status": "approved"}
    return {"payment_id": payment_id, **result}


def reject_payment(db: Session, payment_id: int, actor_id: int, note: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    row = db.execute(text("""
        UPDATE payment_requests SET status='rejected', reviewed_by=:actor,
        reviewed_at=:now, review_note=:note, updated_at=:now
        WHERE id=:id AND status='pending' RETURNING id
    """), {"actor": actor_id, "now": now, "note": note, "id": payment_id}).first()
    if not row:
        raise HTTPException(status_code=409, detail="Payment request is not pending")
    db.commit()
    return {"payment_id": payment_id, "status": "rejected"}
