from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.catalog.pricing_engine import pricing_engine
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module

router = APIRouter(prefix="/catalog/pricing", tags=["Product Pricing Engine"])
GUARDS = [Depends(require_permission("inventory.access")), Depends(require_module("inventory"))]


def _company_for_user(db: Session, company_id: int, user: User) -> None:
    tenant_id = get_effective_tenant_id(user)
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
    if company is None:
        raise HTTPException(status_code=403, detail="Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(status_code=409, detail="Company is inactive")


def _error(exc: ValueError):
    text = str(exc)
    lowered = text.lower()
    status = 404 if "not found" in lowered else 409
    raise HTTPException(status_code=status, detail=text) from exc


@router.get("/resolve", dependencies=GUARDS)
def resolve_price(
    company_id: int = Query(..., gt=0),
    product_id: int = Query(..., gt=0),
    quantity: Decimal = Query(default=Decimal("1"), gt=0),
    price_list_id: int | None = Query(default=None, gt=0),
    at: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    try:
        return pricing_engine.resolve_price(db, company_id, product_id, quantity, price_list_id, at)
    except ValueError as exc:
        _error(exc)


@router.get("/impact", dependencies=GUARDS)
def pricing_impact_all_products(
    company_id: int = Query(..., gt=0),
    target_margin: Decimal = Query(default=Decimal("30"), ge=0, lt=100),
    below_margin: Decimal | None = Query(default=None, ge=0, lt=100),
    price_list_id: int | None = Query(default=None, gt=0),
    quantity: Decimal = Query(default=Decimal("1"), gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    try:
        return pricing_engine.product_wide_impact(
            db, company_id, target_margin, below_margin, price_list_id, quantity
        )
    except ValueError as exc:
        _error(exc)
