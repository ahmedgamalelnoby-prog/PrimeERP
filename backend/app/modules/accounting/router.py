from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.accounting.models import TaxRate

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.post("/tax-rates", status_code=201)
def create_tax(payload: dict, db: Session = Depends(get_db)):
    company_id = int(payload.get("company_id", 0))
    code = str(payload.get("code", "")).strip()
    name = str(payload.get("name", "")).strip()
    rate = Decimal(str(payload.get("rate", 0)))
    tax_type = str(payload.get("tax_type", "vat")).strip().lower()
    is_withholding = bool(payload.get("is_withholding", False))

    if company_id <= 0 or not code or not name:
        raise HTTPException(422, "company_id, code and name are required")
    if rate < 0:
        raise HTTPException(422, "Tax rate cannot be negative")
    if tax_type not in {"vat", "wht", "custom"}:
        raise HTTPException(422, "tax_type must be vat, wht or custom")
    if db.scalar(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.code == code)):
        raise HTTPException(409, "Tax code already exists for this company")

    obj = TaxRate(
        company_id=company_id,
        code=code,
        name=name,
        rate=rate,
        tax_type=tax_type,
        is_withholding=is_withholding,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/tax-rates")
def list_taxes(company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    return list(
        db.scalars(
            select(TaxRate)
            .where(TaxRate.company_id == company_id, TaxRate.is_active.is_(True))
            .order_by(TaxRate.code)
        ).all()
    )
