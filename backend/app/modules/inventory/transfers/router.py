from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.inventory.transfers.schemas import TransferCreate, TransferResponse
from app.modules.inventory.transfers.service import inventory_transfer_service

router = APIRouter(prefix="/inventory/transfers", tags=["Inventory Transfers"])


def _error(exc: ValueError):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[TransferResponse])
def list_transfers(company_id: int = Query(..., gt=0), status: str | None = Query(default=None), db: Session = Depends(get_db)):
    return inventory_transfer_service.list(db, company_id=company_id, status=status)


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    transfer = inventory_transfer_service.get(db, company_id=company_id, transfer_id=transfer_id)
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer


@router.post("", response_model=TransferResponse, status_code=201)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_db)):
    try:
        return inventory_transfer_service.create(db, payload)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/request", response_model=TransferResponse)
def request_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        return inventory_transfer_service.request(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/approve", response_model=TransferResponse)
def approve_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        return inventory_transfer_service.approve(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/ship", response_model=TransferResponse)
def ship_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        return inventory_transfer_service.ship(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/receive", response_model=TransferResponse)
def receive_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        return inventory_transfer_service.receive(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/cancel", response_model=TransferResponse)
def cancel_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        return inventory_transfer_service.cancel(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)
