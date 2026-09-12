from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import UnitOfMeasure
from .schemas import UOMCreate, UOMResponse

router = APIRouter(prefix="/uom", tags=["Units of Measure"])


def _company_for_user(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


@router.post("", response_model=UOMResponse, status_code=201, dependencies=[Depends(require_permission("uom.write"))])
def create_uom(payload: UOMCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    code = payload.code.strip().upper()
    name = payload.name.strip()
    category = payload.category.strip().lower()
    factor = Decimal(payload.factor_to_base)
    if not code or not name or not category:
        raise HTTPException(422, "UOM code, name and category are required")
    if factor <= 0:
        raise HTTPException(422, "UOM conversion factor must be positive")
    if payload.is_base and factor != Decimal("1"):
        raise HTTPException(422, "A base UOM must have factor_to_base equal to 1")
    if db.scalar(select(UnitOfMeasure).where(UnitOfMeasure.company_id == payload.company_id, UnitOfMeasure.code == code)):
        raise HTTPException(409, "UOM code already exists")
    if payload.is_base and db.scalar(select(UnitOfMeasure).where(UnitOfMeasure.company_id == payload.company_id, UnitOfMeasure.category == category, UnitOfMeasure.is_base.is_(True), UnitOfMeasure.is_active.is_(True))):
        raise HTTPException(409, "An active base UOM already exists for this category")
    obj = UnitOfMeasure(company_id=payload.company_id, code=code, name=name, category=category, factor_to_base=factor, is_base=payload.is_base)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[UOMResponse], dependencies=[Depends(require_permission("uom.access"))])
def list_uom(company_id: int = Query(..., gt=0), category: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    q = select(UnitOfMeasure).where(UnitOfMeasure.company_id == company_id, UnitOfMeasure.is_active.is_(True))
    if category:
        q = q.where(UnitOfMeasure.category == category.strip().lower())
    return list(db.scalars(q.order_by(UnitOfMeasure.category, UnitOfMeasure.code)).all())


@router.get("/convert", dependencies=[Depends(require_permission("uom.access"))])
def convert(
    company_id: int,
    from_uom_id: int,
    to_uom_id: int,
    quantity: Decimal = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company_for_user(db, company_id, current_user)
    rows = db.scalars(select(UnitOfMeasure).where(UnitOfMeasure.id.in_([from_uom_id, to_uom_id]), UnitOfMeasure.company_id == company_id, UnitOfMeasure.is_active.is_(True))).all()
    by_id = {x.id: x for x in rows}
    if from_uom_id == to_uom_id:
        if from_uom_id not in by_id:
            raise HTTPException(404, "UOM not found")
        return {"quantity": quantity, "from_uom_id": from_uom_id, "to_uom_id": to_uom_id, "converted_quantity": quantity}
    if len(by_id) != 2:
        raise HTTPException(404, "UOM not found")
    if by_id[from_uom_id].category != by_id[to_uom_id].category:
        raise HTTPException(400, "UOM categories do not match")
    converted = quantity * by_id[from_uom_id].factor_to_base / by_id[to_uom_id].factor_to_base
    return {"quantity": quantity, "from_uom_id": from_uom_id, "to_uom_id": to_uom_id, "converted_quantity": converted}
