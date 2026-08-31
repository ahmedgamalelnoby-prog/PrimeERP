from __future__ import annotations

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.platform.saas_core import require_platform_admin

router = APIRouter(prefix="/platform/saas", tags=["platform-promotions"])


class DiscountCreate(BaseModel):
    name: str
    code: str | None = None
    discount_type: str = "percentage"
    value: Decimal = Field(ge=0)
    scope: str = "global"
    plan_id: int | None = None
    module_id: int | None = None
    tenant_id: int | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    max_uses: int | None = Field(default=None, ge=1)


class OfferCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    discount_id: int
    starts_at: str
    ends_at: str
    is_public: bool = True


class CouponCreate(BaseModel):
    code: str
    discount_id: int
    max_uses: int | None = Field(default=None, ge=1)
    starts_at: str | None = None
    ends_at: str | None = None


@router.get("/discounts")
def discounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_platform_admin(current_user)
    rows = db.execute(text("SELECT * FROM discounts ORDER BY id DESC")).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.post("/discounts")
def create_discount(payload: DiscountCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_platform_admin(current_user)
    row = db.execute(text("""
        INSERT INTO discounts
        (name,code,discount_type,value,scope,plan_id,module_id,tenant_id,starts_at,ends_at,max_uses)
        VALUES (:name,:code,:discount_type,:value,:scope,:plan_id,:module_id,:tenant_id,
                CAST(:starts_at AS timestamptz),CAST(:ends_at AS timestamptz),:max_uses)
        RETURNING *
    """), payload.model_dump()).mappings().one()
    db.commit()
    return dict(row)


@router.get("/offers")
def offers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_platform_admin(current_user)
    rows = db.execute(text("SELECT * FROM offers ORDER BY id DESC")).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.post("/offers")
def create_offer(payload: OfferCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_platform_admin(current_user)
    row = db.execute(text("""
        INSERT INTO offers (name,code,description,discount_id,starts_at,ends_at,is_public,is_active)
        VALUES (:name,:code,:description,:discount_id,CAST(:starts_at AS timestamptz),CAST(:ends_at AS timestamptz),:is_public,true)
        RETURNING *
    """), payload.model_dump()).mappings().one()
    db.commit()
    return dict(row)


@router.get("/coupons")
def coupons(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_platform_admin(current_user)
    rows = db.execute(text("SELECT * FROM coupons ORDER BY id DESC")).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.post("/coupons")
def create_coupon(payload: CouponCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_platform_admin(current_user)
    row = db.execute(text("""
        INSERT INTO coupons (code,discount_id,max_uses,starts_at,ends_at,is_active)
        VALUES (:code,:discount_id,:max_uses,CAST(:starts_at AS timestamptz),CAST(:ends_at AS timestamptz),true)
        RETURNING *
    """), payload.model_dump()).mappings().one()
    db.commit()
    return dict(row)
