from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.commerce.models import BusinessPartner
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import CompanyJurisdiction, Jurisdiction, PartnerJurisdiction, TaxRule
from .schemas import CompanyJurisdictionCreate, JurisdictionCreate, JurisdictionResolveRequest, PartnerJurisdictionCreate, TaxRuleCreate, JurisdictionDecisionResponse
from .service import JurisdictionContext, JurisdictionEngine

router = APIRouter(prefix="/jurisdictions", tags=["Jurisdiction"], dependencies=[Depends(require_permission("commerce.access"))])


def company_for_user(db: Session, company_id: int, user: User):
    obj = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id, Company.is_active.is_(True)))
    if obj is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return obj


def jurisdiction_for_user(db: Session, jurisdiction_id: int):
    obj = db.get(Jurisdiction, jurisdiction_id)
    if obj is None or not obj.is_active:
        raise HTTPException(404, "Jurisdiction not found")
    return obj


@router.post("", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_jurisdiction(payload: JurisdictionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Jurisdictions are platform definitions, but writes remain authenticated and tenant-scoped by permission.
    if current_user.tenant_id is None:
        raise HTTPException(403, "Tenant context is required")
    obj = Jurisdiction(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.post("/company", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def assign_company(payload: CompanyJurisdictionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_for_user(db, payload.company_id, current_user)
    jurisdiction_for_user(db, payload.jurisdiction_id)
    obj = CompanyJurisdiction(**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj


@router.post("/partner", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def assign_partner(payload: PartnerJurisdictionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    partner = db.scalar(select(BusinessPartner).join(Company, Company.id == BusinessPartner.company_id).where(BusinessPartner.id == payload.partner_id, Company.tenant_id == current_user.tenant_id))
    if partner is None:
        raise HTTPException(403, "Partner is outside the current tenant")
    jurisdiction_for_user(db, payload.jurisdiction_id)
    obj = PartnerJurisdiction(**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj


@router.post("/tax-rules", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_tax_rule(payload: TaxRuleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.tenant_id is None:
        raise HTTPException(403, "Tenant context is required")
    jurisdiction_for_user(db, payload.jurisdiction_id)
    obj = TaxRule(**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj


@router.post("/resolve", response_model=JurisdictionDecisionResponse)
def resolve(payload: JurisdictionResolveRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_for_user(db, payload.company_id, current_user)
    ctx = JurisdictionContext(**payload.model_dump())
    try:
        return JurisdictionEngine(db).resolve(ctx)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
