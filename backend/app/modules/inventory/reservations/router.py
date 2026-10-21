from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.inventory.reservations.schemas import ReservationCreate, ReservationResponse
from app.modules.inventory.reservations.service import inventory_reservation_service

router = APIRouter(prefix="/inventory/reservations", tags=["Inventory Reservations"])


@router.get("", response_model=list[ReservationResponse])
def list_reservations(
    company_id: int = Query(..., gt=0),
    item_id: int | None = Query(default=None, gt=0),
    location_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return inventory_reservation_service.list(db, company_id, item_id, location_id)


@router.post("", response_model=ReservationResponse, status_code=201)
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db)):
    try:
        reservation = inventory_reservation_service.reserve(db, payload)
        db.commit()
        db.refresh(reservation)
        return reservation
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/release", response_model=ReservationResponse)
def release_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        reservation = inventory_reservation_service.release(db, company_id=company_id, reservation_id=reservation_id)
        db.commit()
        db.refresh(reservation)
        return reservation
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/consume", response_model=ReservationResponse)
def consume_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        reservation = inventory_reservation_service.consume(db, company_id=company_id, reservation_id=reservation_id)
        db.commit()
        db.refresh(reservation)
        return reservation
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        reservation = inventory_reservation_service.cancel(db, company_id=company_id, reservation_id=reservation_id)
        db.commit()
        db.refresh(reservation)
        return reservation
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
