from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.accounting.models import TaxRate
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
    return company


@router.post("/tax-rates", status_code=201)
def create_tax(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = int(payload.get("company_id", 0))
    _company_for_user(db, company_id, current_user)
    code = str(payload.get("code", "")).strip()
    name = str(payload.get("name", "")).strip()
    rate = Decimal(str(payload.get("rate", 0)))
    tax_type = str(payload.get("tax_type", "vat")).strip().lower()
    is_withholding = bool(payload.get("is_withholding", False))

    if company_id <= 0 or not code or not name:
        raise HTTPException(422, "company_id, code and name are required")
    if rate < 0 or rate > 100:
        raise HTTPException(422, "Tax rate must be between 0 and 100")
    if tax_type not in {"vat", "wht", "custom"}:
        raise HTTPException(422, "tax_type must be vat, wht or custom")
    if tax_type == "wht" and not is_withholding:
        raise HTTPException(422, "WHT tax types must be marked as withholding")
    if is_withholding and tax_type != "wht":
        raise HTTPException(422, "Withholding taxes must use tax_type=wht")
    if db.scalar(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.code == code)):
        raise HTTPException(409, "Tax code already exists for this company")

    obj = TaxRate(company_id=company_id, code=code, name=name, rate=rate, tax_type=tax_type, is_withholding=is_withholding)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/tax-rates")
def list_taxes(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.is_active.is_(True)).order_by(TaxRate.code)).all())
