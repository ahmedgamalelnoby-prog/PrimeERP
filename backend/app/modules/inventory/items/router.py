from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.inventory.items.schemas import InventoryItemCreate, InventoryItemResponse, InventoryItemUpdate
from app.modules.inventory.items.service import inventory_item_service

router = APIRouter(prefix="/inventory/items", tags=["Inventory - Items"])


@router.get("", response_model=list[InventoryItemResponse])
def list_items(company_id: int = Query(gt=0), active_only: bool = True, db: Session = Depends(get_db)):
    return inventory_item_service.list(db, company_id=company_id, active_only=active_only)


@router.get("/{item_id}", response_model=InventoryItemResponse)
def get_item(item_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    item = inventory_item_service.get(db, company_id=company_id, item_id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.post("", response_model=InventoryItemResponse, status_code=201)
def create_item(payload: InventoryItemCreate, db: Session = Depends(get_db)):
    try:
        return inventory_item_service.create(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{item_id}", response_model=InventoryItemResponse)
def update_item(item_id: int, payload: InventoryItemUpdate, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        return inventory_item_service.update(db, company_id=company_id, item_id=item_id, payload=payload)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 409
        raise HTTPException(status_code=status, detail=str(exc)) from exc
