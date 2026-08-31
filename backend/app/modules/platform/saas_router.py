from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.platform.saas_core import (
    activate_subscription,
    approve_payment,
    list_payment_requests,
    list_trials,
    platform_dashboard,
    public_catalog,
    refresh_expired_subscriptions,
    reject_payment,
    require_platform_admin,
)

router = APIRouter(prefix="/platform/saas", tags=["platform-saas"])


class PaymentReview(BaseModel):
    duration_days: int | None = Field(default=None, ge=1, le=3650)
    note: str | None = None


class BankAccountCreate(BaseModel):
    bank_name: str = Field(min_length=1, max_length=150)
    account_name: str = Field(min_length=1, max_length=200)
    account_number: str | None = Field(default=None, max_length=100)
    iban: str | None = Field(default=None, max_length=100)
    swift: str | None = Field(default=None, max_length=30)
    currency_code: str = Field(default="EGP", min_length=3, max_length=3)
    instructions_ar: str | None = None
    instructions_en: str | None = None
    is_primary: bool = False


@router.get("/catalog")
def catalog(db: Session = Depends(get_db)):
    return public_catalog(db)


@router.get("/dashboard")
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    return platform_dashboard(db)


@router.get("/trials")
def trials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    return {"items": list_trials(db)}


@router.post("/subscriptions/{subscription_id}/activate")
def activate(
    subscription_id: int,
    payload: PaymentReview | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    return activate_subscription(
        db,
        subscription_id,
        current_user.id,
        payload.duration_days if payload else None,
    )


@router.get("/payments")
def payments(
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    return {"items": list_payment_requests(db, status_filter)}


@router.post("/payments/{payment_id}/approve")
def approve(
    payment_id: int,
    payload: PaymentReview | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    return approve_payment(
        db,
        payment_id,
        current_user.id,
        payload.duration_days if payload else None,
    )


@router.post("/payments/{payment_id}/reject")
def reject(
    payment_id: int,
    payload: PaymentReview | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    return reject_payment(
        db,
        payment_id,
        current_user.id,
        payload.note if payload else None,
    )


@router.get("/bank-accounts")
def bank_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    rows = db.execute(text("SELECT * FROM bank_accounts ORDER BY is_primary DESC, id")).mappings().all()
    return {"items": [dict(row) for row in rows]}


@router.post("/bank-accounts")
def create_bank_account(
    payload: BankAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    if payload.is_primary:
        db.execute(text("UPDATE bank_accounts SET is_primary=false WHERE is_primary=true"))
    row = db.execute(text("""
        INSERT INTO bank_accounts
        (bank_name, account_name, account_number, iban, swift, currency_code,
         instructions_ar, instructions_en, is_primary, is_active)
        VALUES (:bank_name,:account_name,:account_number,:iban,:swift,:currency_code,
                :instructions_ar,:instructions_en,:is_primary,true)
        RETURNING *
    """), payload.model_dump()).mappings().one()
    db.commit()
    return dict(row)


@router.post("/maintenance/expire")
def expire_now(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    return {"updated": refresh_expired_subscriptions(db)}
