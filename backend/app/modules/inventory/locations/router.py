from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.inventory.locations.schemas import LocationCreate, LocationResponse, LocationUpdate
from app.modules.inventory.locations.service import location_service

router = APIRouter(prefix="/inventory/locations", tags=["Inventory - Locations"])


@router.get("", response_model=list[LocationResponse])
def list_locations(
    company_id: int = Query(gt=0),
    warehouse_id: int = Query(gt=0),
    db: Session = Depends(get_db),
):
    try:
        return location_service.list(db, company_id=company_id, warehouse_id=warehouse_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=LocationResponse, status_code=201)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    try:
        return location_service.create(db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    payload: LocationUpdate,
    company_id: int = Query(gt=0),
    db: Session = Depends(get_db),
):
    try:
        return location_service.update(db, company_id=company_id, location_id=location_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
