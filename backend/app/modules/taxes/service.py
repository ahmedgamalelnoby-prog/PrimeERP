"""Application service for tax calculations and tax master validation."""

from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.accounting.tax_engine import calculate_taxes

from .constants import MAX_TAX_RATE, MIN_TAX_RATE, TAX_TYPES, WHT_TAX_TYPE
from .crud import get_tax_by_code


def normalize_tax_master(*, code: str, name: str, rate, tax_type: str = "vat", is_withholding: bool = False) -> dict:
    code = str(code).strip().upper()
    name = str(name).strip()
    tax_type = str(tax_type).strip().lower()
    if not code or not name:
        raise HTTPException(422, "code and name are required")
    try:
        rate = Decimal(str(rate))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise HTTPException(422, "rate must be a valid decimal") from exc
    if not rate.is_finite() or rate < MIN_TAX_RATE or rate > MAX_TAX_RATE:
        raise HTTPException(422, "Tax rate must be between 0 and 100")
    if tax_type not in TAX_TYPES:
        raise HTTPException(422, "tax_type must be vat, wht or custom")
    if (tax_type == WHT_TAX_TYPE) != bool(is_withholding):
        raise HTTPException(422, "WHT and withholding flags must be consistent")
    return {"code": code, "name": name, "rate": rate, "tax_type": tax_type, "is_withholding": bool(is_withholding)}


def ensure_unique_code(db: Session, company_id: int, code: str, *, exclude_id: int | None = None) -> None:
    tax = get_tax_by_code(db, company_id, code)
    if tax is not None and tax.id != exclude_id:
        raise HTTPException(409, "Tax code already exists for this company")


def calculate(db: Session, *, company_id: int, amount: Decimal, tax_ids: list[int], inclusive: bool = False) -> dict:
    return calculate_taxes(db, company_id=company_id, amount=amount, tax_ids=tax_ids, inclusive=inclusive)
