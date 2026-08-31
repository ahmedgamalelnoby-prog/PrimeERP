from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.platform.saas_core import require_platform_admin

router = APIRouter(prefix="/platform/saas", tags=["platform-billing"])


class PaymentRequestCreate(BaseModel):
    subscription_id: int
    invoice_id: int | None = None
    bank_account_id: int | None = None
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(default="EGP", min_length=3, max_length=3)
    payment_method: str = Field(default="bank_transfer", max_length=30)
    reference: str | None = Field(default=None, max_length=100)
    proof_file: str | None = Field(default=None, max_length=500)


class PlanUpsert(BaseModel):
    name_ar: str
    name_en: str
    code: str
    description_ar: str | None = None
    description_en: str | None = None
    monthly_price: Decimal = Field(ge=0)
    yearly_price: Decimal = Field(ge=0)
    currency_code: str = Field(default="EGP", min_length=3, max_length=3)
    trial_days: int = Field(default=14, ge=0, le=365)
    max_users: int = Field(default=5, ge=1)
    max_companies: int = Field(default=1, ge=1)
    max_branches: int = Field(default=1, ge=1)
    max_products: int = Field(default=1000, ge=0)
    max_integrations: int = Field(default=1, ge=0)
    storage_limit_mb: int = Field(default=1024, ge=0)
    is_public: bool = True
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)


class ModulePriceUpsert(BaseModel):
    module_id: int
    currency_code: str = Field(default="EGP", min_length=3, max_length=3)
    monthly_base_price: Decimal = Field(default=0, ge=0)
    yearly_base_price: Decimal = Field(default=0, ge=0)
    monthly_user_price: Decimal = Field(default=0, ge=0)
    yearly_user_price: Decimal = Field(default=0, ge=0)


class PlatformSettingUpdate(BaseModel):
    value: str
    description: str | None = None
    is_public: bool = False


@router.get("/payment-methods")
def public_payment_methods(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT id, bank_name, account_name, account_number, iban, swift,
               currency_code, instructions_ar, instructions_en
        FROM bank_accounts WHERE is_active=true
        ORDER BY is_primary DESC, id
    """)).mappings().all()
    return {"bank_accounts": [dict(r) for r in rows]}


@router.post("/payments/request")
def create_payment_request(
    payload: PaymentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_platform_admin:
        raise HTTPException(status_code=400, detail="Platform admins cannot create customer payment requests")
    if not current_user.tenant_id:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    subscription = db.execute(text("SELECT id, tenant_id, status FROM subscriptions WHERE id=:id"), {"id": payload.subscription_id}).mappings().first()
    if not subscription or subscription["tenant_id"] != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    row = db.execute(text("""
        INSERT INTO payment_requests
        (tenant_id, subscription_id, invoice_id, bank_account_id, amount, currency_code,
         payment_method, reference, proof_file, status)
        VALUES (:tenant_id,:subscription_id,:invoice_id,:bank_account_id,:amount,:currency_code,
                :payment_method,:reference,:proof_file,'pending')
        RETURNING *
    """), {**payload.model_dump(), "tenant_id": current_user.tenant_id}).mappings().one()
    db.commit()
    return dict(row)


@router.get("/plans")
def list_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    rows = db.execute(text("SELECT * FROM subscription_plans ORDER BY display_order, id")).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.post("/plans")
def create_plan(
    payload: PlanUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    row = db.execute(text("""
        INSERT INTO subscription_plans
        (name_ar,name_en,code,description_ar,description_en,monthly_price,yearly_price,currency_code,
         trial_days,max_users,max_companies,max_branches,max_products,max_integrations,storage_limit_mb,
         is_public,is_active,display_order)
        VALUES (:name_ar,:name_en,:code,:description_ar,:description_en,:monthly_price,:yearly_price,:currency_code,
                :trial_days,:max_users,:max_companies,:max_branches,:max_products,:max_integrations,:storage_limit_mb,
                :is_public,:is_active,:display_order)
        RETURNING *
    """), payload.model_dump()).mappings().one()
    db.commit()
    return dict(row)


@router.patch("/plans/{plan_id}")
def update_plan(
    plan_id: int,
    payload: PlanUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    values = payload.model_dump()
    values["id"] = plan_id
    row = db.execute(text("""
        UPDATE subscription_plans SET
          name_ar=:name_ar,name_en=:name_en,code=:code,description_ar=:description_ar,description_en=:description_en,
          monthly_price=:monthly_price,yearly_price=:yearly_price,currency_code=:currency_code,trial_days=:trial_days,
          max_users=:max_users,max_companies=:max_companies,max_branches=:max_branches,max_products=:max_products,
          max_integrations=:max_integrations,storage_limit_mb=:storage_limit_mb,is_public=:is_public,
          is_active=:is_active,display_order=:display_order,updated_at=now()
        WHERE id=:id RETURNING *
    """), values).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.commit()
    return dict(row)


@router.put("/module-prices/{module_id}")
def upsert_module_price(
    module_id: int,
    payload: ModulePriceUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    if payload.module_id != module_id:
        raise HTTPException(status_code=400, detail="Module id mismatch")
    row = db.execute(text("""
        INSERT INTO module_prices
        (module_id,currency_code,monthly_base_price,yearly_base_price,monthly_user_price,yearly_user_price,is_active)
        VALUES (:module_id,:currency_code,:monthly_base_price,:yearly_base_price,:monthly_user_price,:yearly_user_price,true)
        ON CONFLICT (module_id,currency_code) DO UPDATE SET
          monthly_base_price=excluded.monthly_base_price,
          yearly_base_price=excluded.yearly_base_price,
          monthly_user_price=excluded.monthly_user_price,
          yearly_user_price=excluded.yearly_user_price,
          is_active=true
        RETURNING *
    """), payload.model_dump()).mappings().one()
    db.commit()
    return dict(row)


@router.get("/settings")
def settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    rows = db.execute(text("SELECT id,key,value,description,is_public,updated_by,updated_at FROM platform_settings ORDER BY key")).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.put("/settings/{key}")
def update_setting(
    key: str,
    payload: PlatformSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_platform_admin(current_user)
    row = db.execute(text("""
        INSERT INTO platform_settings (key,value,description,is_public,updated_by)
        VALUES (:key,:value,:description,:is_public,:updated_by)
        ON CONFLICT (key) DO UPDATE SET value=excluded.value,description=excluded.description,
          is_public=excluded.is_public,updated_by=excluded.updated_by,updated_at=now()
        RETURNING *
    """), {"key": key, **payload.model_dump(), "updated_by": current_user.id}).mappings().one()
    db.commit()
    return dict(row)
