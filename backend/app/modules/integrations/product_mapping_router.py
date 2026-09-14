from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from .product_mapping_service import archive_mapping, create_mapping, list_mappings, mark_synced, update_mapping
from .models import IntegrationProductMapping

router = APIRouter(
    prefix="/integrations/product-mappings",
    tags=["Integration Product Mappings"],
    dependencies=[Depends(require_permission("integrations.access")), Depends(require_module("integrations"))],
)

class ProductMappingCreate(BaseModel):
    company_id: int = Field(gt=0)
    connection_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    external_id: str = Field(min_length=1, max_length=160)
    external_sku: str | None = Field(default=None, max_length=160)
    external_url: str | None = Field(default=None, max_length=500)
    sync_direction: str = Field(default="bidirectional", max_length=20)

class ProductMappingUpdate(BaseModel):
    external_id: str | None = Field(default=None, min_length=1, max_length=160)
    external_sku: str | None = Field(default=None, max_length=160)
    external_url: str | None = Field(default=None, max_length=500)
    sync_direction: str | None = Field(default=None, max_length=20)
    sync_status: str | None = Field(default=None, max_length=20)

class ProductMappingResponse(BaseModel):
    id: int
    company_id: int
    connection_id: int
    product_id: int
    variant_id: int | None
    external_id: str
    external_sku: str | None
    external_url: str | None
    sync_direction: str
    sync_status: str
    last_synced_at: datetime | None
    class Config:
        from_attributes = True

def _check_company(user: User, company_id: int, db: Session) -> int:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    allowed = db.scalar(
        select(Company.id).where(
            Company.id == company_id,
            Company.tenant_id == user.tenant_id,
            Company.is_active.is_(True),
        )
    )
    if allowed is None:
        raise HTTPException(404, "Company not found")
    return allowed

def _errors(exc: ValueError):
    raise HTTPException(422, str(exc)) from exc

@router.post("", response_model=ProductMappingResponse, status_code=201, dependencies=[Depends(require_permission("integrations.write"))])
def create(payload: ProductMappingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_company(current_user, payload.company_id, db)
    try:
        return create_mapping(db, **payload.model_dump())
    except ValueError as exc:
        _errors(exc)

@router.get("", response_model=list[ProductMappingResponse])
def listing(company_id: int = Query(..., gt=0), connection_id: int = Query(..., gt=0), product_id: int | None = Query(default=None, gt=0), variant_id: int | None = Query(default=None, gt=0), status: str | None = Query(default=None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_company(current_user, company_id, db)
    try:
        return list_mappings(db, company_id=company_id, connection_id=connection_id, product_id=product_id, variant_id=variant_id, status=status)
    except ValueError as exc:
        _errors(exc)

def _company_from_mapping(db: Session, mapping_id: int, user: User) -> int:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    row = db.scalar(
        select(IntegrationProductMapping.company_id)
        .join(Company, Company.id == IntegrationProductMapping.company_id)
        .where(
            IntegrationProductMapping.id == mapping_id,
            Company.tenant_id == user.tenant_id,
            Company.is_active.is_(True),
        )
    )
    if row is None:
        raise HTTPException(404, "Product mapping not found")
    return row

@router.get("/by-external", response_model=list[ProductMappingResponse])
def by_external(
    company_id: int = Query(..., gt=0),
    connection_id: int = Query(..., gt=0),
    external_id: str = Query(..., min_length=1, max_length=160),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_company(current_user, company_id, db)
    try:
        from .product_mapping_service import find_by_external_id
        return find_by_external_id(db, company_id=company_id, connection_id=connection_id, external_id=external_id)
    except ValueError as exc:
        _errors(exc)

@router.get("/by-product", response_model=list[ProductMappingResponse])
def by_product(
    company_id: int = Query(..., gt=0),
    connection_id: int = Query(..., gt=0),
    product_id: int = Query(..., gt=0),
    variant_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_company(current_user, company_id, db)
    try:
        from .product_mapping_service import find_by_product
        return find_by_product(db, company_id=company_id, connection_id=connection_id, product_id=product_id, variant_id=variant_id)
    except ValueError as exc:
        _errors(exc)

@router.put("/{mapping_id}", response_model=ProductMappingResponse, dependencies=[Depends(require_permission("integrations.write"))])
def update(mapping_id: int, payload: ProductMappingUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        company_id = _company_from_mapping(db, mapping_id, current_user)
        return update_mapping(db, company_id=company_id, mapping_id=mapping_id, **payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        _errors(exc)

@router.post("/{mapping_id}/archive", response_model=ProductMappingResponse, dependencies=[Depends(require_permission("integrations.write"))])
def archive(mapping_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = _company_from_mapping(db, mapping_id, current_user)
    try:
        return archive_mapping(db, company_id=company_id, mapping_id=mapping_id)
    except ValueError as exc:
        _errors(exc)

@router.post("/{mapping_id}/mark-synced", response_model=ProductMappingResponse, dependencies=[Depends(require_permission("integrations.write"))])
def synced(mapping_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_id = _company_from_mapping(db, mapping_id, current_user)
    try:
        return mark_synced(db, company_id=company_id, mapping_id=mapping_id)
    except ValueError as exc:
        _errors(exc)
