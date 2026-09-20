"""Canonical tax-domain API."""

from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.models import TaxRate
from app.modules.accounting.tax_engine import calculate_taxes
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.commerce.models import SalesDocument, SalesLine, PurchaseDocument, PurchaseLine
from app.modules.saas.entitlements import require_module
from .models import TaxReturnDraft

router = APIRouter(prefix="/taxes", tags=["taxes"], dependencies=[Depends(require_module("accounting"))])


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    tenant_id = get_effective_tenant_id(user)
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
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
    return {"code": code, "name": name, "rate": rate, "tax_type": tax_type, "is_withholding": is_withholding}


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
        db.commit(); db.refresh(obj)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "Tax code already exists for this company") from exc
    return obj


@router.get("/rates", dependencies=[Depends(require_permission("tax.access"))])
def list_taxes(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(TaxRate).where(TaxRate.company_id == company_id).order_by(TaxRate.is_active.desc(), TaxRate.code)).all())


@router.post("/calculate", dependencies=[Depends(require_permission("tax.access"))])
def calculate_tax(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        company_id = int(payload.get("company_id", 0)); amount = Decimal(str(payload.get("amount", "0"))); tax_ids = [int(value) for value in payload.get("tax_ids", [])]; inclusive = bool(payload.get("inclusive", False))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise HTTPException(422, "company_id, amount and tax_ids must be valid values") from exc
    _company_for_user(db, company_id, current_user)
    return calculate_taxes(db, company_id=company_id, amount=amount, tax_ids=tax_ids, inclusive=inclusive)


@router.patch("/rates/{tax_id}", dependencies=[Depends(require_permission("tax.write"))])
def update_tax(tax_id: int, payload: dict, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tax = _tax_for_company(db, tax_id, company_id, current_user)
    values = _validated_values({"code": payload.get("code", tax.code), "name": payload.get("name", tax.name), "rate": payload.get("rate", tax.rate), "tax_type": payload.get("tax_type", tax.tax_type), "is_withholding": payload.get("is_withholding", tax.is_withholding)})
    duplicate = db.scalar(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.code == values["code"], TaxRate.id != tax.id))
    if duplicate: raise HTTPException(409, "Tax code already exists for this company")
    for key, value in values.items(): setattr(tax, key, value)
    if "is_active" in payload: tax.is_active = bool(payload["is_active"])
    try:
        db.commit(); db.refresh(tax)
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(409, "Tax code already exists for this company") from exc
    return tax


@router.delete("/rates/{tax_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("tax.write"))])
def deactivate_tax(tax_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tax = _tax_for_company(db, tax_id, company_id, current_user)
    tax.is_active = False
    db.commit()


def _return_values(payload: dict) -> dict:
    try:
        period_from = date.fromisoformat(str(payload["period_from"]))
        period_to = date.fromisoformat(str(payload["period_to"]))
        output_vat = Decimal(str(payload.get("output_vat", 0)))
        input_vat = Decimal(str(payload.get("input_vat", 0)))
        adjustments = Decimal(str(payload.get("adjustments", 0)))
        wht_payable = Decimal(str(payload.get("wht_payable", 0)))
        reconciliation_difference = Decimal(str(payload.get("reconciliation_difference", 0)))
    except (KeyError, ValueError, InvalidOperation, TypeError) as exc:
        raise HTTPException(422, "Invalid tax-return period or decimal values") from exc
    if period_to < period_from:
        raise HTTPException(422, "period_to must be on or after period_from")
    decimals = (output_vat, input_vat, adjustments, wht_payable, reconciliation_difference)
    if any(not value.is_finite() for value in decimals):
        raise HTTPException(422, "Tax-return values must be finite")
    net_vat = output_vat - input_vat + adjustments
    return {"period_from": period_from, "period_to": period_to, "output_vat": output_vat, "input_vat": input_vat, "adjustments": adjustments, "wht_payable": wht_payable, "net_vat": net_vat, "reconciliation_difference": reconciliation_difference, "is_reconciled": reconciliation_difference == 0}


@router.post("/returns/preview", dependencies=[Depends(require_permission("tax.access"))])
def preview_tax_return(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = int(payload.get("company_id", 0))
    _company_for_user(db, company_id, current_user)
    values = _return_values(payload)
    return {"company_id": company_id, **values, "submission_status": "not_supported_by_this_endpoint"}


@router.post("/returns/drafts", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("tax.write"))])
def create_tax_return_draft(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = int(payload.get("company_id", 0))
    _company_for_user(db, company_id, current_user)
    values = _return_values(payload)
    jurisdiction = str(payload.get("jurisdiction_code", "EG")).upper()
    overlap = db.scalar(select(TaxReturnDraft).where(
        TaxReturnDraft.company_id == company_id,
        TaxReturnDraft.jurisdiction_code == jurisdiction,
        TaxReturnDraft.period_from <= values["period_to"],
        TaxReturnDraft.period_to >= values["period_from"],
        TaxReturnDraft.status.notin_({"rejected", "cancelled"}),
    ))
    if overlap is not None:
        raise HTTPException(409, "An active tax return already covers an overlapping period")
    obj = TaxReturnDraft(company_id=company_id, jurisdiction_code=jurisdiction, **values, notes=payload.get("notes"))
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.post("/returns/drafts/{draft_id}/reconcile", dependencies=[Depends(require_permission("tax.write"))])
def reconcile_tax_return(draft_id:int, company_id:int=Query(...,gt=0), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj=db.scalar(select(TaxReturnDraft).where(TaxReturnDraft.id==draft_id,TaxReturnDraft.company_id==company_id).with_for_update())
    if obj is None: raise HTTPException(404,"Tax return draft not found")
    if obj.status not in {"draft","reconciled"}: raise HTTPException(409,"Tax return cannot be reconciled in its current state")
    if Decimal(obj.reconciliation_difference or 0) != 0: raise HTTPException(409,"Tax return has a non-zero reconciliation difference")
    obj.is_reconciled=True; obj.status="reconciled"; db.commit(); db.refresh(obj); return obj

@router.post("/returns/drafts/{draft_id}/submit", dependencies=[Depends(require_permission("tax.write"))])
def submit_tax_return(draft_id:int, company_id:int=Query(...,gt=0), submission_reference:str|None=None, current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj=db.scalar(select(TaxReturnDraft).where(TaxReturnDraft.id==draft_id,TaxReturnDraft.company_id==company_id).with_for_update())
    if obj is None: raise HTTPException(404,"Tax return draft not found")
    if obj.status!="reconciled" or not obj.is_reconciled: raise HTTPException(409,"Tax return must be reconciled before submission")
    if obj.status=="submitted": return obj
    obj.status="submitted"; obj.submission_status="submitted"; obj.submission_reference=submission_reference or obj.submission_reference
    db.commit(); db.refresh(obj); return obj

@router.post("/returns/drafts/{draft_id}/accept", dependencies=[Depends(require_permission("tax.write"))])
def accept_tax_return(draft_id:int, company_id:int=Query(...,gt=0), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj=db.scalar(select(TaxReturnDraft).where(TaxReturnDraft.id==draft_id,TaxReturnDraft.company_id==company_id).with_for_update())
    if obj is None: raise HTTPException(404,"Tax return draft not found")
    if obj.status!="submitted": raise HTTPException(409,"Only submitted tax returns can be accepted")
    obj.status="accepted"; obj.submission_status="accepted"; db.commit(); db.refresh(obj); return obj

@router.post("/returns/drafts/{draft_id}/close", dependencies=[Depends(require_permission("tax.write"))])
def close_tax_return(draft_id:int, company_id:int=Query(...,gt=0), current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj=db.scalar(select(TaxReturnDraft).where(TaxReturnDraft.id==draft_id,TaxReturnDraft.company_id==company_id).with_for_update())
    if obj is None: raise HTTPException(404,"Tax return draft not found")
    if obj.status!="accepted": raise HTTPException(409,"Only accepted tax returns can be closed")
    obj.status="closed"; obj.submission_status="closed"; db.commit(); db.refresh(obj); return obj


@router.get("/returns/drafts", dependencies=[Depends(require_permission("tax.access"))])
def list_tax_return_drafts(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(TaxReturnDraft).where(TaxReturnDraft.company_id == company_id).order_by(TaxReturnDraft.id.desc()).limit(200)).all())


@router.post("/returns/preview-from-ledger", dependencies=[Depends(require_permission("tax.access"))])
def preview_tax_return_from_ledger(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = int(payload.get("company_id", 0))
    _company_for_user(db, company_id, current_user)
    try:
        period_from = date.fromisoformat(str(payload["period_from"]))
        period_to = date.fromisoformat(str(payload["period_to"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(422, "Valid period_from and period_to are required") from exc
    if period_to < period_from:
        raise HTTPException(422, "period_to must be on or after period_from")
    sales = db.scalars(select(SalesDocument).where(
        SalesDocument.company_id == company_id,
        SalesDocument.document_date >= period_from,
        SalesDocument.document_date <= period_to,
        SalesDocument.document_type.in_(["invoice", "credit_note"]),
        SalesDocument.status.in_(["posted", "fulfilled", "partially_fulfilled"]),
    )).all()
    purchases = db.scalars(select(PurchaseDocument).where(
        PurchaseDocument.company_id == company_id,
        PurchaseDocument.document_date >= period_from,
        PurchaseDocument.document_date <= period_to,
        PurchaseDocument.document_type.in_(["bill", "debit_note"]),
        PurchaseDocument.status.in_(["posted", "received", "partially_received"]),
    )).all()
    output_vat = Decimal("0"); input_vat = Decimal("0"); wht = Decimal("0")
    sales_credit = Decimal("0"); purchase_debit = Decimal("0")
    for doc in sales:
        sign = Decimal("-1") if doc.document_type == "credit_note" else Decimal("1")
        for line in doc.lines:
            taxes = list(db.scalars(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.id.in_(list(line.tax_rate_ids or [])))).all()) if line.tax_rate_ids else []
            base = Decimal(line.quantity or 0) * Decimal(line.unit_price or 0) * (Decimal("1") - Decimal(line.discount_percent or 0)/Decimal("100"))
            for tax in taxes:
                amount = base * Decimal(tax.rate or 0) / Decimal("100")
                if tax.is_withholding: wht += sign * amount
                else: output_vat += sign * amount
            if sign < 0: sales_credit += abs(base)
    for doc in purchases:
        sign = Decimal("-1") if doc.document_type == "debit_note" else Decimal("1")
        for line in doc.lines:
            taxes = list(db.scalars(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.id.in_(list(line.tax_rate_ids or [])))).all()) if line.tax_rate_ids else []
            base = Decimal(line.quantity or 0) * Decimal(line.unit_price or 0) * (Decimal("1") - Decimal(line.discount_percent or 0)/Decimal("100"))
            for tax in taxes:
                amount = base * Decimal(tax.rate or 0) / Decimal("100")
                if tax.is_withholding: wht += sign * amount
                else: input_vat += sign * amount
            if sign < 0: purchase_debit += abs(base)
    net_vat = output_vat - input_vat
    return {
        "company_id": company_id, "period_from": period_from, "period_to": period_to,
        "source_documents": {"sales": len(sales), "purchases": len(purchases)},
        "output_vat": output_vat, "input_vat": input_vat, "net_vat": net_vat,
        "wht_payable": wht, "sales_credit_base": sales_credit, "purchase_debit_base": purchase_debit,
        "reconciliation_difference": Decimal("0"), "is_reconciled": True,
    }
