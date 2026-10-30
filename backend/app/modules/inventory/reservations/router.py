from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.inventory.access import accessible_warehouse_ids, require_location_access
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.reservations.models import InventoryReservation
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.reservations.schemas import ReservationCreate, ReservationResponse
from app.modules.inventory.reservations.service import inventory_reservation_service

router = APIRouter(prefix="/inventory/reservations", tags=["Inventory Reservations"], dependencies=[Depends(require_permission("inventory.access"))])


def _company_for_user(db: Session, company_id: int, user: User):
    if get_effective_tenant_id(user) is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == get_effective_tenant_id(user), Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


def _authorize_reservation(db: Session, user: User, company_id: int, reservation_id: int):
    reservation = db.scalar(
        select(InventoryReservation).where(
            InventoryReservation.id == reservation_id,
            InventoryReservation.company_id == company_id,
        )
    )
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    require_location_access(db, user, company_id, reservation.location_id)
    return reservation


@router.get("")
def list_reservations(company_id: int = Query(..., gt=0), item_id: int | None = Query(default=None, gt=0), location_id: int | None = Query(default=None, gt=0), variant_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    if location_id is not None:
        require_location_access(db, current_user, company_id, location_id)
        return inventory_reservation_service.list(db, company_id, item_id, location_id, variant_id)
    allowed = accessible_warehouse_ids(db, current_user, company_id)
    if allowed is None:
        return inventory_reservation_service.list(db, company_id, item_id, location_id, variant_id)
    if not allowed:
        return []
    stmt = (
        select(InventoryReservation)
        .join(InventoryLocation, InventoryLocation.id == InventoryReservation.location_id)
        .where(
            InventoryReservation.company_id == company_id,
            InventoryLocation.warehouse_id.in_(allowed),
        )
    )
    if item_id is not None:
        stmt = stmt.where(InventoryReservation.item_id == item_id)
    if variant_id is not None:
        stmt = stmt.where(InventoryReservation.variant_id == variant_id)
    return list(db.scalars(stmt.order_by(InventoryReservation.id.desc())).all())


@router.post("", response_model=ReservationResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, current_user)
    require_location_access(db, current_user, payload.company_id, payload.location_id)
    try:
        reservation = inventory_reservation_service.reserve(db, payload)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/release", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.write"))])
def release_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    _authorize_reservation(db, current_user, company_id, reservation_id)
    try:
        reservation = inventory_reservation_service.release(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/consume", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.post"))])
def consume_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    _authorize_reservation(db, current_user, company_id, reservation_id)
    try:
        reservation = inventory_reservation_service.consume(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.write"))])
def cancel_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    _authorize_reservation(db, current_user, company_id, reservation_id)
    try:
        reservation = inventory_reservation_service.cancel(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
