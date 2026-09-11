from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.inventory.warehouses.schemas import WarehouseCreate, WarehouseResponse, WarehouseUpdate
from app.modules.inventory.warehouses.service import warehouse_service

router = APIRouter(prefix="/inventory/warehouses", tags=["Inventory - Warehouses"])


@router.get("", response_model=list[WarehouseResponse])
def list_warehouses(
    tenant_id: int = Query(gt=0),
    company_id: int = Query(gt=0),
    branch_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return warehouse_service.list(db, tenant_id=tenant_id, company_id=company_id, branch_id=branch_id)


@router.get("/central", response_model=WarehouseResponse | None)
def get_central_warehouse(
    tenant_id: int = Query(gt=0),
    company_id: int = Query(gt=0),
    db: Session = Depends(get_db),
):
    return warehouse_service.get_central(db, tenant_id=tenant_id, company_id=company_id)


@router.post("", response_model=WarehouseResponse, status_code=201)
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db)):
    try:
        return warehouse_service.create(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    tenant_id: int = Query(gt=0),
    db: Session = Depends(get_db),
):
    try:
        return warehouse_service.update(db, tenant_id=tenant_id, warehouse_id=warehouse_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
