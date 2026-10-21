from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.transfers.schemas import TransferCreate, TransferResponse
from app.modules.inventory.transfers.service import inventory_transfer_service

router = APIRouter(
    prefix="/inventory/transfers",
    tags=["Inventory Transfers"],
    dependencies=[Depends(require_permission("inventory.access"))],
)


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    if get_effective_tenant_id(user) is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == get_effective_tenant_id(user)))
    if company is None:
        raise HTTPException(status_code=403, detail="Company is outside the current tenant")
    return company


def _error(exc: ValueError):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[TransferResponse])
def list_transfers(
    company_id: int = Query(..., gt=0),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    return inventory_transfer_service.list(db, company_id=company_id, status=status)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(
    transfer_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    transfer = inventory_transfer_service.get(db, company_id=company_id, transfer_id=transfer_id)
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer


@router.post("", response_model=TransferResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_transfer(
    payload: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, payload.company_id, current_user)
    try:
        return inventory_transfer_service.create(db, payload)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/request", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.write"))])
def request_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return inventory_transfer_service.request(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/approve", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.post"))])
def approve_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return inventory_transfer_service.approve(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/ship", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.post"))])
def ship_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return inventory_transfer_service.ship(db, company_id=company_id, transfer_id=transfer_id, tenant_id=get_effective_tenant_id(current_user), user_id=current_user.id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/receive", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.post"))])
def receive_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return inventory_transfer_service.receive(db, company_id=company_id, transfer_id=transfer_id, tenant_id=get_effective_tenant_id(current_user), user_id=current_user.id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/cancel", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.write"))])
def cancel_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return inventory_transfer_service.cancel(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)
