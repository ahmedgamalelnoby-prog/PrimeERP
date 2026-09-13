from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.items.schemas import InventoryItemCreate, InventoryItemResponse, InventoryItemUpdate
from app.modules.inventory.items.service import inventory_item_service
from app.modules.saas.entitlements import require_module

router = APIRouter(prefix="/inventory/items", tags=["Inventory - Items"])


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(status_code=403, detail="Company is outside the current tenant")
    return company


@router.get("", response_model=list[InventoryItemResponse], dependencies=[Depends(require_permission("inventory.access")), Depends(require_module("inventory"))])
def list_items(
    company_id: int = Query(..., gt=0),
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    return inventory_item_service.list(db, company_id=company_id, active_only=active_only)


@router.get("/{item_id}", response_model=InventoryItemResponse, dependencies=[Depends(require_permission("inventory.access")), Depends(require_module("inventory"))])
def get_item(
    item_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    item = inventory_item_service.get(db, company_id=company_id, item_id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.get("/{item_id}/stock", dependencies=[Depends(require_permission("inventory.access")), Depends(require_module("inventory"))])
def get_item_stock(
    item_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    item = inventory_item_service.get(db, company_id=company_id, item_id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return inventory_item_service.stock(db, company_id=company_id, item_id=item_id)


@router.post("", response_model=InventoryItemResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write")), Depends(require_module("inventory"))])
def create_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _company_for_user(db, payload.company_id, current_user)
    try:
        return inventory_item_service.create(db, payload, tenant_id=company.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{item_id}", response_model=InventoryItemResponse, dependencies=[Depends(require_permission("inventory.write")), Depends(require_module("inventory"))])
def update_item(
    item_id: int,
    payload: InventoryItemUpdate,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    try:
        return inventory_item_service.update(db, company_id=company_id, item_id=item_id, payload=payload)
    except ValueError as exc:
        error_status = 404 if "not found" in str(exc).lower() else 409
        raise HTTPException(status_code=error_status, detail=str(exc)) from exc
