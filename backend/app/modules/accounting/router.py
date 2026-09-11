from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.models import TaxRate
from app.modules.accounting.schemas import TaxRateCreate, TaxRateResponse, TaxRateUpdate
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

router = APIRouter(prefix="/accounting", tags=["accounting"])


def _company_for_user(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(409, "Company is inactive")
    return company


def _tax_for_company(db: Session, tax_id: int, company_id: int, user: User) -> TaxRate:
    _company_for_user(db, company_id, user)
    tax = db.scalar(select(TaxRate).where(TaxRate.id == tax_id, TaxRate.company_id == company_id))
    if tax is None:
        raise HTTPException(404, "Tax rate not found")
    return tax


@router.post("/tax-rates", response_model=TaxRateResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("tax.write"))])
def create_tax(payload: TaxRateCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    values = payload.model_dump()
    code = values["code"].strip().upper()
    if db.scalar(select(TaxRate).where(TaxRate.company_id == payload.company_id, TaxRate.code == code)):
        raise HTTPException(409, "Tax code already exists for this company")
    obj = TaxRate(**values, code=code)
    db.add(obj)
    try:
        db.commit()
        db.refresh(obj)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Tax code already exists for this company") from exc
    return obj


@router.get("/tax-rates", response_model=list[TaxRateResponse], dependencies=[Depends(require_permission("tax.access"))])
def list_taxes(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(TaxRate).where(TaxRate.company_id == company_id).order_by(TaxRate.is_active.desc(), TaxRate.code)).all())


@router.patch("/tax-rates/{tax_id}", response_model=TaxRateResponse, dependencies=[Depends(require_permission("tax.write"))])
def update_tax(tax_id: int, payload: TaxRateUpdate, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tax = _tax_for_company(db, tax_id, company_id, current_user)
    values = payload.model_dump(exclude_unset=True)
    merged = {
        "code": values.get("code", tax.code),
        "name": values.get("name", tax.name),
        "rate": values.get("rate", tax.rate),
        "tax_type": values.get("tax_type", tax.tax_type),
        "is_withholding": values.get("is_withholding", tax.is_withholding),
    }
    from app.modules.accounting.schemas import TaxRateBase
    validated = TaxRateBase.model_validate(merged)
    code = validated.code.strip().upper()
    duplicate = db.scalar(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.code == code, TaxRate.id != tax.id))
    if duplicate:
        raise HTTPException(409, "Tax code already exists for this company")
    for key in ("code", "name", "rate", "tax_type", "is_withholding"):
        setattr(tax, key, getattr(validated, key) if key != "code" else code)
    if "is_active" in values:
        tax.is_active = values["is_active"]
    try:
        db.commit()
        db.refresh(tax)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Tax code already exists for this company") from exc
    return tax


@router.delete("/tax-rates/{tax_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("tax.write"))])
def deactivate_tax(tax_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tax = _tax_for_company(db, tax_id, company_id, current_user)
    tax.is_active = False
    db.commit()
