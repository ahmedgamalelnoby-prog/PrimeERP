import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.catalog.schemas import BarcodeResponse, VariantBarcodeCreate, VariantCreate, VariantResponse
from app.modules.catalog.variant_lifecycle_service import product_variant_lifecycle_service
from app.modules.catalog.variant_service import product_variant_service
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module

router = APIRouter(prefix="/catalog", tags=["Product Catalog - Variants"])
GUARDS = [Depends(require_permission("inventory.access")), Depends(require_module("inventory"))]
WRITE_GUARDS = [Depends(require_permission("inventory.write")), Depends(require_module("inventory"))]


def _company_for_user(db: Session, company_id: int, user: User) -> None:
    tenant_id = get_effective_tenant_id(user)
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
    if company is None:
        raise HTTPException(status_code=403, detail="Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(status_code=409, detail="Company is inactive")


def _error(exc: ValueError):
    text = str(exc)
    lowered = text.lower()
    status = 404 if "not found" in lowered else 409
    raise HTTPException(status_code=status, detail=text) from exc


def _variant_response(variant):
    try:
        attributes = json.loads(variant.attributes or "{}")
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="Stored variant attributes are invalid JSON") from exc
    return {
        "id": variant.id, "company_id": variant.company_id, "product_id": variant.product_id,
        "sku": variant.sku, "name_ar": variant.name_ar, "name_en": variant.name_en,
        "attributes": attributes, "uom_id": variant.uom_id, "sales_price": variant.sales_price,
        "purchase_price": variant.purchase_price, "is_active": variant.is_active,
        "created_at": variant.created_at, "updated_at": variant.updated_at,
        "barcodes": list(variant.barcodes or []),
    }


@router.post("/products/{product_id}/variants", response_model=VariantResponse, status_code=201, dependencies=WRITE_GUARDS)
def create_variant(product_id: int, payload: VariantCreate, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    if payload.product_id != product_id:
        raise HTTPException(status_code=422, detail="Payload product_id must match the URL product_id")
    try:
        return _variant_response(product_variant_service.create_variant(db, company_id, payload))
    except ValueError as exc:
        _error(exc)


@router.get("/products/{product_id}/variants", response_model=list[VariantResponse], dependencies=GUARDS)
def list_product_variants(product_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return [_variant_response(v) for v in product_variant_service.list_variants(db, company_id, product_id)]
    except ValueError as exc:
        _error(exc)


@router.get("/variants", response_model=list[VariantResponse], dependencies=GUARDS)
def list_variants(company_id: int = Query(..., gt=0), product_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return [_variant_response(v) for v in product_variant_service.list_variants(db, company_id, product_id)]
    except ValueError as exc:
        _error(exc)


@router.get("/variants/{variant_id}", response_model=VariantResponse, dependencies=GUARDS)
def get_variant(variant_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return _variant_response(product_variant_service.get_variant(db, company_id, variant_id))
    except ValueError as exc:
        _error(exc)


@router.put("/variants/{variant_id}", response_model=VariantResponse, dependencies=WRITE_GUARDS)
def update_variant(variant_id: int, payload: VariantCreate, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return _variant_response(product_variant_lifecycle_service.update_variant(db, company_id, variant_id, payload))
    except ValueError as exc:
        _error(exc)


@router.post("/variants/{variant_id}/deactivate", response_model=VariantResponse, dependencies=WRITE_GUARDS)
def deactivate_variant(variant_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return _variant_response(product_variant_lifecycle_service.deactivate_variant(db, company_id, variant_id))
    except ValueError as exc:
        _error(exc)


@router.post("/variants/{variant_id}/reactivate", response_model=VariantResponse, dependencies=WRITE_GUARDS)
def reactivate_variant(variant_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return _variant_response(product_variant_lifecycle_service.reactivate_variant(db, company_id, variant_id))
    except ValueError as exc:
        _error(exc)


@router.post("/variants/{variant_id}/barcodes", response_model=BarcodeResponse, status_code=201, dependencies=WRITE_GUARDS)
def add_variant_barcode(variant_id: int, payload: VariantBarcodeCreate, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return product_variant_service.add_barcode(db, company_id, variant_id, payload)
    except ValueError as exc:
        _error(exc)


@router.post("/barcodes/{barcode_id}/deactivate", response_model=BarcodeResponse, dependencies=WRITE_GUARDS)
def deactivate_barcode(barcode_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return product_variant_lifecycle_service.deactivate_barcode(db, company_id, barcode_id)
    except ValueError as exc:
        _error(exc)


@router.post("/barcodes/{barcode_id}/reactivate", response_model=BarcodeResponse, dependencies=WRITE_GUARDS)
def reactivate_barcode(barcode_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return product_variant_lifecycle_service.reactivate_barcode(db, company_id, barcode_id)
    except ValueError as exc:
        _error(exc)


@router.get("/barcodes", response_model=list[BarcodeResponse], dependencies=GUARDS)
def list_barcodes(company_id: int = Query(..., gt=0), product_id: int | None = Query(default=None, gt=0), variant_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return product_variant_service.list_barcodes(db, company_id, product_id, variant_id)
    except ValueError as exc:
        _error(exc)
