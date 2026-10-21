from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.warehouses.schemas import WarehouseCreate, WarehouseResponse, WarehouseUpdate
from app.modules.inventory.warehouses.service import warehouse_service
from app.modules.saas.entitlements import require_module

router = APIRouter(prefix="/inventory/warehouses", tags=["Inventory - Warehouses"], dependencies=[Depends(require_module("inventory"))])


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    if get_effective_tenant_id(user) is None: raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == get_effective_tenant_id(user), Company.is_active.is_(True)))
    if company is None: raise HTTPException(status_code=403, detail="Company is outside the current tenant")
    return company


@router.get("", response_model=list[WarehouseResponse], dependencies=[Depends(require_permission("inventory.access"))])
def list_warehouses(company_id: int = Query(gt=0), branch_id: int | None = Query(default=None, gt=0), include_central: bool = True, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user); return warehouse_service.list(db, company_id=company_id, branch_id=branch_id, include_central=include_central)


@router.get("/central", response_model=WarehouseResponse | None, dependencies=[Depends(require_permission("inventory.access"))])
def get_central_warehouse(company_id: int = Query(gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user); return warehouse_service.get_central(db, company_id=company_id)


@router.post("", response_model=WarehouseResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = _company_for_user(db, payload.company_id, current_user)
    if payload.tenant_id != company.tenant_id: raise HTTPException(status_code=422, detail="Warehouse tenant does not match company tenant")
    try:
        return warehouse_service.create(db, tenant_id=company.tenant_id, company_id=company.id, branch_id=payload.branch_id, code=payload.code, name=payload.name, description=payload.description, is_central=payload.is_central)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{warehouse_id}", response_model=WarehouseResponse, dependencies=[Depends(require_permission("inventory.write"))])
def update_warehouse(warehouse_id: int, payload: WarehouseUpdate, company_id: int = Query(gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    warehouse = warehouse_service.get(db, company_id=company_id, warehouse_id=warehouse_id)
    if warehouse is None: raise HTTPException(status_code=404, detail="Warehouse not found")
    if payload.name is not None: warehouse.name = payload.name.strip()
    if payload.description is not None: warehouse.description = payload.description
    if payload.is_active is not None: warehouse.is_active = payload.is_active
    db.flush(); return warehouse
