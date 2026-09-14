"""Canonical tax-domain API.

The accounting module still owns the persisted TaxRate model for backwards
compatibility. This router exposes the tax domain under /taxes without
creating a second tax table or a second implementation of tax calculations.
"""

from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.models import TaxRate
from app.modules.accounting.tax_engine import calculate_taxes
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module

router = APIRouter(
    prefix="/taxes",
    tags=["taxes"],
    dependencies=[Depends(require_module("accounting"))],
)


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == user.tenant_id,
        )
    )
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(409, "Company is inactive")
    return company


def _tax_for_company(db: Session, tax_id: int, company_id: int, user: User) -> TaxRate:
    _company_for_user(db, company_id, user)
    tax = db.scalar(
        select(TaxRate).where(
            TaxRate.id == tax_id,
            TaxRate.company_id == company_id,
        )
    )
    if tax is None:
        raise HTTPException(404, "Tax rate not found")
    return tax


def _validated_values(payload: dict) -> dict:
    code = str(payload.get("code", "")).strip().upper()
    name = str(payload.get("name", "")).strip()
    tax_type = str(payload.get("tax_type", "vat")).strip().lower()
    is_withholding = bool(payload.get("is_withholding", False))
    if not code or not name:
        raise HTTPException(422, "code and name are required")
    try:
        rate = Decimal(str(payload.get("rate", 0)))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise HTTPException(422, "rate must be a valid decimal") from exc
    if not rate.is_finite() or rate < 0 or rate > 100:
        raise HTTPException(422, "Tax rate must be between 0 and 100")
    if tax_type not in {"vat", "wht", "custom"}:
        raise HTTPException(422, "tax_type must be vat, wht or custom")
    if tax_type == "wht" and not is_withholding:
        raise HTTPException(422, "WHT tax types must be marked as withholding")
    if is_withholding and tax_type != "wht":
        raise HTTPException(422, "Withholding taxes must use tax_type=wht")
    return {
        "code": code,
        "name": name,
        "rate": rate,
        "tax_type": tax_type,
        "is_withholding": is_withholding,
    }


@router.post("/rates", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("tax.write"))])
def create_tax(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = int(payload.get("company_id", 0))
    _company_for_user(db, company_id, current_user)
    values = _validated_values(payload)
    if db.scalar(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.code == values["code"])):
        raise HTTPException(409, "Tax code already exists for this company")
    obj = TaxRate(company_id=company_id, **values)
    db.add(obj)
    try:
        db.commit()
        db.refresh(obj)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Tax code already exists for this company") from exc
    return obj


@router.get("/rates", dependencies=[Depends(require_permission("tax.access"))])
def list_taxes(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(
        db.scalars(
            select(TaxRate)
            .where(TaxRate.company_id == company_id)
            .order_by(TaxRate.is_active.desc(), TaxRate.code)
        ).all()
    )


@router.post("/calculate", dependencies=[Depends(require_permission("tax.access"))])
def calculate_tax(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        company_id = int(payload.get("company_id", 0))
        amount = Decimal(str(payload.get("amount", "0")))
        tax_ids = [int(value) for value in payload.get("tax_ids", [])]
        inclusive = bool(payload.get("inclusive", False))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise HTTPException(422, "company_id, amount and tax_ids must be valid values") from exc
    _company_for_user(db, company_id, current_user)
    return calculate_taxes(db, company_id=company_id, amount=amount, tax_ids=tax_ids, inclusive=inclusive)


@router.patch("/rates/{tax_id}", dependencies=[Depends(require_permission("tax.write"))])
def update_tax(tax_id: int, payload: dict, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tax = _tax_for_company(db, tax_id, company_id, current_user)
    values = _validated_values(
        {
            "code": payload.get("code", tax.code),
            "name": payload.get("name", tax.name),
            "rate": payload.get("rate", tax.rate),
            "tax_type": payload.get("tax_type", tax.tax_type),
            "is_withholding": payload.get("is_withholding", tax.is_withholding),
        }
    )
    duplicate = db.scalar(
        select(TaxRate).where(
            TaxRate.company_id == company_id,
            TaxRate.code == values["code"],
            TaxRate.id != tax.id,
        )
    )
    if duplicate:
        raise HTTPException(409, "Tax code already exists for this company")
    for key, value in values.items():
        setattr(tax, key, value)
    if "is_active" in payload:
        tax.is_active = bool(payload["is_active"])
    try:
        db.commit()
        db.refresh(tax)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Tax code already exists for this company") from exc
    return tax


@router.delete("/rates/{tax_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("tax.write"))])
def deactivate_tax(tax_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tax = _tax_for_company(db, tax_id, company_id, current_user)
    tax.is_active = False
    db.commit()
