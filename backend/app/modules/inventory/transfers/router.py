from app.core.context.access import require_company_access, require_branch_access
from app.core.context import get_optional_request_context
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
from app.modules.inventory.transfers.models import InventoryTransfer
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.branches.membership import BranchUserMembership

router = APIRouter(
    prefix="/inventory/transfers",
    tags=["Inventory Transfers"],
    dependencies=[Depends(require_permission("inventory.access"))],
)


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    return require_company_access(db, company_id, user)
def _error(exc: ValueError):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


def _assert_warehouse_pair_access(db: Session, company_id: int, source_id: int, destination_id: int, user: User) -> None:
    branch_ids: set[int] = set()
    for warehouse_id in (source_id, destination_id):
        warehouse = db.scalar(select(InventoryWarehouse).where(
            InventoryWarehouse.id == warehouse_id,
            InventoryWarehouse.company_id == company_id,
            InventoryWarehouse.is_active.is_(True),
        ))
        if warehouse is None:
            raise HTTPException(404, "Transfer warehouse not found")
        if warehouse.branch_id is not None:
            branch_ids.add(warehouse.branch_id)
    if user.is_platform_admin:
        return
    context = get_optional_request_context()
    if context is None or context.branch_id not in branch_ids:
        raise HTTPException(403, "Select one of the transfer branches using X-Branch-ID")
    for branch_id in branch_ids:
        require_branch_access(db, company_id, branch_id, user, require_selected=False)


def _assert_transfer_access(db: Session, company_id: int, transfer: InventoryTransfer, user: User) -> None:
    _assert_warehouse_pair_access(
        db, company_id, transfer.source_warehouse_id, transfer.destination_warehouse_id, user
    )


@router.get("", response_model=list[TransferResponse])
def list_transfers(
    company_id: int = Query(..., gt=0),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    transfers = inventory_transfer_service.list(db, company_id=company_id, status=status)
    if current_user.is_platform_admin:
        return transfers
    visible_branch_ids = set(db.scalars(
        select(BranchUserMembership.branch_id).where(
            BranchUserMembership.user_id == current_user.id,
            BranchUserMembership.is_active.is_(True),
        )
    ).all())
    visible = []
    for transfer in transfers:
        source = db.get(InventoryWarehouse, transfer.source_warehouse_id)
        destination = db.get(InventoryWarehouse, transfer.destination_warehouse_id)
        if source is None or destination is None:
            continue
        if all(w.branch_id is None or w.branch_id in visible_branch_ids for w in (source, destination)):
            visible.append(transfer)
    return visible


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
    _assert_transfer_access(db, company_id, transfer, current_user)
    return transfer


@router.post("", response_model=TransferResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_transfer(
    payload: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, payload.company_id, current_user)
    _assert_warehouse_pair_access(
        db, payload.company_id, payload.source_warehouse_id, payload.destination_warehouse_id, current_user
    )
    try:
        return inventory_transfer_service.create(db, payload)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/request", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.write"))])
def request_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    transfer = inventory_transfer_service.get(db, company_id=company_id, transfer_id=transfer_id)
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    _assert_transfer_access(db, company_id, transfer, current_user)
    try:
        return inventory_transfer_service.request(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/approve", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.post"))])
def approve_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    transfer = inventory_transfer_service.get(db, company_id=company_id, transfer_id=transfer_id)
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    _assert_transfer_access(db, company_id, transfer, current_user)
    try:
        return inventory_transfer_service.approve(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/ship", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.post"))])
def ship_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    transfer = inventory_transfer_service.get(db, company_id=company_id, transfer_id=transfer_id)
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    _assert_transfer_access(db, company_id, transfer, current_user)
    try:
        return inventory_transfer_service.ship(db, company_id=company_id, transfer_id=transfer_id, tenant_id=get_effective_tenant_id(current_user), user_id=current_user.id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/receive", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.post"))])
def receive_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    transfer = inventory_transfer_service.get(db, company_id=company_id, transfer_id=transfer_id)
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    _assert_transfer_access(db, company_id, transfer, current_user)
    try:
        return inventory_transfer_service.receive(db, company_id=company_id, transfer_id=transfer_id, tenant_id=get_effective_tenant_id(current_user), user_id=current_user.id)
    except ValueError as exc:
        _error(exc)


@router.post("/{transfer_id}/cancel", response_model=TransferResponse, dependencies=[Depends(require_permission("inventory.write"))])
def cancel_transfer(transfer_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    transfer = inventory_transfer_service.get(db, company_id=company_id, transfer_id=transfer_id)
    if transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    _assert_transfer_access(db, company_id, transfer, current_user)
    try:
        return inventory_transfer_service.cancel(db, company_id=company_id, transfer_id=transfer_id)
    except ValueError as exc:
        _error(exc)
