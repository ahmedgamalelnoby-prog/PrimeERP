from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.shipping.accounting_service import shipping_accounting_service
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
