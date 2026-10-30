from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context.access import require_company_access, require_branch_access
from app.core.context import get_optional_request_context
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.reservations.schemas import ReservationCreate, ReservationResponse
from app.modules.inventory.reservations.service import inventory_reservation_service
from app.modules.inventory.reservations.models import InventoryReservation
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.warehouses.models import InventoryWarehouse

router = APIRouter(prefix="/inventory/reservations", tags=["Inventory Reservations"], dependencies=[Depends(require_permission("inventory.access"))])


def _company_for_user(db: Session, company_id: int, user: User):
    return require_company_access(db, company_id, user)
def _selected_branch(db: Session, company_id: int, user: User) -> int | None:
    if user.is_platform_admin:
        return None
    context = get_optional_request_context()
    if context is None or context.branch_id is None:
        raise HTTPException(400, "Select a branch using X-Branch-ID before accessing reservations")
    require_branch_access(db, company_id, context.branch_id, user)
    return context.branch_id


def _assert_location_access(db: Session, company_id: int, location_id: int, user: User) -> None:
    location = db.scalar(select(InventoryLocation).where(
        InventoryLocation.id == location_id,
        InventoryLocation.company_id == company_id,
        InventoryLocation.is_active.is_(True),
    ))
    if location is None:
        raise HTTPException(404, "Stock location not found")
    warehouse = db.scalar(select(InventoryWarehouse).where(
        InventoryWarehouse.id == location.warehouse_id,
        InventoryWarehouse.company_id == company_id,
        InventoryWarehouse.is_active.is_(True),
    ))
    if warehouse is None:
        raise HTTPException(404, "Stock warehouse not found")
    if warehouse.branch_id is not None:
        require_branch_access(db, company_id, warehouse.branch_id, user)


def _assert_reservation_access(db: Session, company_id: int, reservation_id: int, user: User) -> None:
    reservation = db.scalar(select(InventoryReservation).where(
        InventoryReservation.id == reservation_id,
        InventoryReservation.company_id == company_id,
    ))
    if reservation is None:
        raise HTTPException(404, "Reservation not found")
    _assert_location_access(db, company_id, reservation.location_id, user)


@router.get("")
def list_reservations(company_id: int = Query(..., gt=0), item_id: int | None = Query(default=None, gt=0), location_id: int | None = Query(default=None, gt=0), variant_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    branch_id = _selected_branch(db, company_id, current_user)
    if location_id is not None:
        _assert_location_access(db, company_id, location_id, current_user)
    return inventory_reservation_service.list(db, company_id, item_id, location_id, variant_id, branch_id=branch_id)


@router.post("", response_model=ReservationResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, current_user)
    _selected_branch(db, payload.company_id, current_user)
    _assert_location_access(db, payload.company_id, payload.location_id, current_user)
    try:
        reservation = inventory_reservation_service.reserve(db, payload)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/release", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.write"))])
def release_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    _selected_branch(db, company_id, current_user)
    _assert_reservation_access(db, company_id, reservation_id, current_user)
    try:
        reservation = inventory_reservation_service.release(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/consume", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.post"))])
def consume_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    _selected_branch(db, company_id, current_user)
    _assert_reservation_access(db, company_id, reservation_id, current_user)
    try:
        reservation = inventory_reservation_service.consume(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse, dependencies=[Depends(require_permission("inventory.write"))])
def cancel_reservation(reservation_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    _selected_branch(db, company_id, current_user)
    _assert_reservation_access(db, company_id, reservation_id, current_user)
    try:
        reservation = inventory_reservation_service.cancel(db, company_id=company_id, reservation_id=reservation_id)
        db.commit(); db.refresh(reservation); return reservation
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
