from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.reservations.schemas import ReservationCreate, ReservationResponse
from app.modules.inventory.reservations.service import inventory_reservation_service

router = APIRouter(prefix="/inventory/reservations", tags=["Inventory Reservations"], dependencies=[Depends(require_permission("inventory.access"))])


def _company_for_user(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


@router.get("")
def list_reservations(company_id: int = Query(..., gt=0), item_id: int | None = Query(default=None, gt=0), location_id: int | None = Query(default=None, gt=0), variant_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    return inventory_reservation_service.list(db, company_id, item_id, location_id, variant_id)


@router.post("", response_model=ReservationResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, current_user)
    try:
        reservation = inventory_reservation_service.reserve(db, payload)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/release", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.write"))])
def release_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        reservation = inventory_reservation_service.release(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/consume", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.post"))])
def consume_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        reservation = inventory_reservation_service.consume(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.write"))])
def cancel_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        reservation = inventory_reservation_service.cancel(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
