from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission, require_platform_admin
from app.database.session import get_db
from app.modules.commerce.models import BusinessPartner
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import CompanyJurisdiction, Jurisdiction, PartnerJurisdiction, TaxRule
from .schemas import CompanyJurisdictionCreate, JurisdictionCreate, JurisdictionResolveRequest, PartnerJurisdictionCreate, TaxRuleCreate, JurisdictionDecisionResponse
from .service import JurisdictionContext, JurisdictionEngine

router = APIRouter(prefix="/jurisdictions", tags=["Jurisdiction"], dependencies=[Depends(require_permission("commerce.access"))])

_OVERLAP_CONSTRAINTS = {
    "company_jurisdiction_effective_no_overlap": "Overlapping active company jurisdiction version exists",
    "partner_jurisdiction_effective_no_overlap": "Overlapping active partner jurisdiction version exists",
    "jurisdiction_tax_rule_effective_no_overlap": "Overlapping active tax rule version exists for this legal rule code",
}


def company_for_user(db: Session, company_id: int, user: User):
    obj = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == get_effective_tenant_id(user), Company.is_active.is_(True)))
    if obj is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return obj


def partner_for_user(db: Session, partner_id: int, user: User):
    obj = db.scalar(
        select(BusinessPartner)
        .join(Company, Company.id == BusinessPartner.company_id)
        .where(BusinessPartner.id == partner_id, Company.tenant_id == get_effective_tenant_id(user))
    )
    if obj is None:
        raise HTTPException(403, "Partner is outside the current tenant")
    return obj


def jurisdiction_for_user(db: Session, jurisdiction_id: int):
    obj = db.get(Jurisdiction, jurisdiction_id)
    if obj is None or not obj.is_active:
        raise HTTPException(404, "Jurisdiction not found")
    return obj


def _overlap_clause(model, start, end):
    starts_before_end = True if end is None else model.effective_from <= end
    ends_after_start = or_(model.effective_to.is_(None), model.effective_to >= start)
    return and_(starts_before_end, ends_after_start, model.is_active.is_(True))


def _reject_overlap(db: Session, model, identity_filters, start, end, message):
    query = select(model).where(and_(*identity_filters, _overlap_clause(model, start, end))).with_for_update()
    if db.scalar(query) is not None:
        raise HTTPException(409, message)


def _commit_version(db: Session, obj):
    try:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except IntegrityError as exc:
        db.rollback()
        diag = getattr(getattr(exc, "orig", None), "diag", None)
        constraint_name = getattr(diag, "constraint_name", None)
        message = _OVERLAP_CONSTRAINTS.get(constraint_name)
        if message:
            raise HTTPException(409, message) from exc
        raise


@router.post("", status_code=201, dependencies=[Depends(require_permission("commerce.write")), Depends(require_platform_admin())])
def create_jurisdiction(payload: JurisdictionCreate, db: Session = Depends(get_db)):
    obj = Jurisdiction(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.post("/company", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def assign_company(payload: CompanyJurisdictionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_for_user(db, payload.company_id, current_user)
    jurisdiction_for_user(db, payload.jurisdiction_id)
    _reject_overlap(db, CompanyJurisdiction, [CompanyJurisdiction.company_id == payload.company_id, CompanyJurisdiction.jurisdiction_id == payload.jurisdiction_id, CompanyJurisdiction.role == payload.role], payload.effective_from, payload.effective_to, _OVERLAP_CONSTRAINTS["company_jurisdiction_effective_no_overlap"])
    return _commit_version(db, CompanyJurisdiction(**payload.model_dump()))


@router.post("/partner", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def assign_partner(payload: PartnerJurisdictionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    partner_for_user(db, payload.partner_id, current_user)
    jurisdiction_for_user(db, payload.jurisdiction_id)
    _reject_overlap(db, PartnerJurisdiction, [PartnerJurisdiction.partner_id == payload.partner_id, PartnerJurisdiction.jurisdiction_id == payload.jurisdiction_id, PartnerJurisdiction.role == payload.role], payload.effective_from, payload.effective_to, _OVERLAP_CONSTRAINTS["partner_jurisdiction_effective_no_overlap"])
    return _commit_version(db, PartnerJurisdiction(**payload.model_dump()))


@router.post("/tax-rules", status_code=201, dependencies=[Depends(require_permission("commerce.write")), Depends(require_platform_admin())])
def create_tax_rule(payload: TaxRuleCreate, db: Session = Depends(get_db)):
    jurisdiction_for_user(db, payload.jurisdiction_id)
    _reject_overlap(db, TaxRule, [TaxRule.jurisdiction_id == payload.jurisdiction_id, TaxRule.code == payload.code], payload.effective_from, payload.effective_to, _OVERLAP_CONSTRAINTS["jurisdiction_tax_rule_effective_no_overlap"])
    return _commit_version(db, TaxRule(**payload.model_dump()))


@router.post("/resolve", response_model=JurisdictionDecisionResponse)
def resolve(payload: JurisdictionResolveRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_for_user(db, payload.company_id, current_user)
    if payload.partner_id is not None:
        partner_for_user(db, payload.partner_id, current_user)
    ctx = JurisdictionContext(**payload.model_dump())
    try:
        return JurisdictionEngine(db).resolve(ctx)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
