from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.inventory.warehouses.schemas import WarehouseCreate, WarehouseResponse, WarehouseUpdate
from app.modules.inventory.warehouses.service import warehouse_service

router = APIRouter(prefix="/inventory/warehouses", tags=["Inventory - Warehouses"])


@router.get("", response_model=list[WarehouseResponse])
def list_warehouses(
    company_id: int = Query(gt=0),
    branch_id: int | None = Query(default=None, gt=0),
    include_central: bool = True,
    db: Session = Depends(get_db),
):
    return warehouse_service.list(
        db,
        company_id=company_id,
        branch_id=branch_id,
        include_central=include_central,
    )


@router.get("/central", response_model=WarehouseResponse | None)
def get_central_warehouse(
    company_id: int = Query(gt=0),
    db: Session = Depends(get_db),
):
    return warehouse_service.get_central(db, company_id=company_id)


@router.post("", response_model=WarehouseResponse, status_code=201)
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db)):
    try:
        return warehouse_service.create(
            db,
            tenant_id=payload.tenant_id,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            code=payload.code,
            name=payload.name,
            description=payload.description,
            is_central=payload.is_central,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    company_id: int = Query(gt=0),
    db: Session = Depends(get_db),
):
    warehouse = warehouse_service.get(db, company_id=company_id, warehouse_id=warehouse_id)
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    if payload.name is not None:
        warehouse.name = payload.name.strip()
    if payload.description is not None:
        warehouse.description = payload.description
    if payload.is_active is not None:
        warehouse.is_active = payload.is_active
    db.flush()
    return warehouse
