from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.shipping.models import ShippingCarrier
from app.modules.shipping.pricing_models import ShippingPricingProfile, ShippingPricingRule
from app.modules.shipping.pricing_schemas import (
    PricingProfileCreate, PricingProfileResponse, PricingRuleCreate, PricingRuleResponse,
    ShippingCostInput, ShippingCostResponse,
)
from app.modules.shipping.pricing_service import shipping_pricing_service

router = APIRouter(
    prefix="/shipping/pricing", tags=["Shipping Pricing"],
    dependencies=[Depends(require_permission("shipping.access")), Depends(require_module("shipping"))],
)


def _company(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    obj = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id, Company.is_active.is_(True)))
    if obj is None:
        raise HTTPException(403, "Company is outside the current tenant or inactive")
    return obj


@router.post("/profiles", response_model=PricingProfileResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def create_profile(payload: PricingProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    carrier = db.scalar(select(ShippingCarrier).where(ShippingCarrier.id == payload.carrier_id, ShippingCarrier.company_id == payload.company_id, ShippingCarrier.is_active.is_(True)))
    if carrier is None:
        raise HTTPException(422, "Carrier does not belong to the company or is inactive")
    obj = ShippingPricingProfile(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/profiles", response_model=list[PricingProfileResponse])
def list_profiles(company_id: int = Query(..., gt=0), carrier_id: int | None = Query(default=None, gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    stmt = select(ShippingPricingProfile).where(ShippingPricingProfile.company_id == company_id, ShippingPricingProfile.is_active.is_(True))
    if carrier_id:
        stmt = stmt.where(ShippingPricingProfile.carrier_id == carrier_id)
    return list(db.scalars(stmt.order_by(ShippingPricingProfile.priority.asc(), ShippingPricingProfile.effective_from.desc())).all())


@router.post("/rules", response_model=PricingRuleResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def create_rule(payload: PricingRuleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    profile = db.scalar(select(ShippingPricingProfile).join(Company, Company.id == ShippingPricingProfile.company_id).where(
        ShippingPricingProfile.id == payload.profile_id, Company.tenant_id == current_user.tenant_id, ShippingPricingProfile.is_active.is_(True)
    ))
    if profile is None:
        raise HTTPException(404, "Pricing profile not found")
    obj = ShippingPricingRule(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/rules", response_model=list[PricingRuleResponse])
def list_rules(profile_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    profile = db.scalar(select(ShippingPricingProfile).join(Company, Company.id == ShippingPricingProfile.company_id).where(
        ShippingPricingProfile.id == profile_id, Company.tenant_id == current_user.tenant_id
    ))
    if profile is None:
        raise HTTPException(404, "Pricing profile not found")
    return list(db.scalars(select(ShippingPricingRule).where(ShippingPricingRule.profile_id == profile_id, ShippingPricingRule.is_active.is_(True)).order_by(ShippingPricingRule.priority.asc(), ShippingPricingRule.id.asc())).all())


@router.post("/calculate", response_model=ShippingCostResponse)
def calculate(payload: ShippingCostInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    try:
        return shipping_pricing_service.calculate(db, payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
