from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.purchasing.suppliers.schemas import SupplierCreate, SupplierResponse, SupplierUpdate
from app.modules.purchasing.suppliers.service import supplier_service

router = APIRouter(prefix="/purchasing/suppliers", tags=["Purchasing - Suppliers"])


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(company_id: int = Query(gt=0), active_only: bool = True, db: Session = Depends(get_db)):
    return supplier_service.list(db, company_id, active_only)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    supplier = supplier_service.get(db, company_id, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.post("", response_model=SupplierResponse, status_code=201)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    try:
        supplier = supplier_service.create(db, payload)
        db.commit()
        db.refresh(supplier)
        return supplier
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: int, payload: SupplierUpdate, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        supplier = supplier_service.update(db, company_id, supplier_id, payload)
        db.commit()
        db.refresh(supplier)
        return supplier
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
