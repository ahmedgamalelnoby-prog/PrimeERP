from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.modules.branches.access import can_manage_all_branches, require_branch_access
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.shipping.accounting_service import shipping_accounting_service
from app.modules.shipping.models import ShippingCarrier
from app.modules.shipping.settlement_models import ShippingSettlementBatch

router = APIRouter(
    prefix="/shipping/settlements",
    tags=["Shipping Settlement Accounting"],
    dependencies=[Depends(require_permission("shipping.access")), Depends(require_module("shipping"))],
)


@router.post("/{batch_id}/post", status_code=201, dependencies=[Depends(require_permission("shipping.post"))])
def post_settlement(
    batch_id: int,
    company_id: int = Query(..., gt=0),
    posting_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == current_user.tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    batch = db.scalar(select(ShippingSettlementBatch).where(ShippingSettlementBatch.id == batch_id, ShippingSettlementBatch.company_id == company_id))
    if batch is None:
        raise HTTPException(404, "Settlement batch not found")
    carrier = db.scalar(select(ShippingCarrier).where(
        ShippingCarrier.id == batch.carrier_id,
        ShippingCarrier.company_id == company_id,
    ))
    if carrier is None:
        raise HTTPException(404, "Carrier not found for settlement batch")
    if carrier.branch_id is None:
        if not can_manage_all_branches(db, current_user):
            raise HTTPException(403, "Central carrier access requires tenant-wide branch management permission")
    else:
        branch = require_branch_access(db, current_user, carrier.branch_id)
        if branch.company_id != company_id:
            raise HTTPException(404, "Carrier not found for settlement batch")
    try:
        entry = shipping_accounting_service.post_settlement(db, batch_id=batch.id, user_id=current_user.id, posting_date=posting_date)
        db.commit()
        db.refresh(entry)
        return {"batch_id": batch.id, "journal_entry_id": entry.id, "status": entry.status}
    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
