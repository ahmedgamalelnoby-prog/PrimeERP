from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.catalog.bundle_service import product_bundle_service
from app.modules.catalog.schemas import BundleCreate, BundleResponse
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module

router = APIRouter(prefix="/catalog", tags=["Product Catalog - Bundles"])
GUARDS = [Depends(require_permission("inventory.access")), Depends(require_module("inventory"))]
WRITE = [Depends(require_permission("inventory.write")), Depends(require_module("inventory"))]


def guard_company(db, company_id, user):
    tenant_id = get_effective_tenant_id(user)
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id, Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(status_code=403, detail="Company is outside the current tenant or inactive")


def err(exc):
    text = str(exc)
    raise HTTPException(status_code=404 if "not found" in text.lower() else 409, detail=text) from exc


def response(bundle):
    return {"id": bundle.id, "company_id": bundle.company_id, "product_id": bundle.product_id, "code": bundle.code, "name_ar": bundle.name_ar, "name_en": bundle.name_en, "is_active": bundle.is_active, "lines": [{"id": x.id, "line_no": x.line_no, "component_product_id": x.component_product_id, "quantity": x.quantity} for x in bundle.lines]}


@router.post("/bundles", response_model=BundleResponse, status_code=201, dependencies=WRITE)
def create_bundle(payload: BundleCreate, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    guard_company(db, company_id, current_user)
    if payload.company_id != company_id:
        raise HTTPException(status_code=422, detail="Payload company_id must match query company_id")
    try:
        return response(product_bundle_service.create(db, company_id, payload))
    except ValueError as exc:
        err(exc)


@router.get("/bundles", response_model=list[BundleResponse], dependencies=GUARDS)
def list_bundles(company_id: int = Query(..., gt=0), active_only: bool = True, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    guard_company(db, company_id, current_user)
    return [response(x) for x in product_bundle_service.list(db, company_id, active_only)]


@router.get("/bundles/{bundle_id}", response_model=BundleResponse, dependencies=GUARDS)
def get_bundle(bundle_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    guard_company(db, company_id, current_user)
    try:
        return response(product_bundle_service.get(db, company_id, bundle_id))
    except ValueError as exc:
        err(exc)


@router.post("/bundles/{bundle_id}/deactivate", response_model=BundleResponse, dependencies=WRITE)
def deactivate_bundle(bundle_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    guard_company(db, company_id, current_user)
    try:
        return response(product_bundle_service.deactivate(db, company_id, bundle_id))
    except ValueError as exc:
        err(exc)


@router.post("/bundles/{bundle_id}/reactivate", response_model=BundleResponse, dependencies=WRITE)
def reactivate_bundle(bundle_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    guard_company(db, company_id, current_user)
    try:
        return response(product_bundle_service.reactivate(db, company_id, bundle_id))
    except ValueError as exc:
        err(exc)


@router.get("/bundles/{bundle_id}/availability", dependencies=GUARDS)
def bundle_availability(bundle_id: int, company_id: int = Query(..., gt=0), warehouse_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    guard_company(db, company_id, current_user)
    try:
        return product_bundle_service.availability(db, company_id, bundle_id, warehouse_id)
    except ValueError as exc:
        err(exc)
