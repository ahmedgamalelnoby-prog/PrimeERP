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
from app.modules.inventory.costing.schemas import InventoryValuationResponse
from app.modules.inventory.costing.service import inventory_costing_service

router = APIRouter(
    prefix="/inventory/costing",
    tags=["Inventory Costing"],
    dependencies=[Depends(require_permission("inventory.access"))],
)


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    return require_company_access(db, company_id, user)
@router.get("/valuation", response_model=InventoryValuationResponse)
def inventory_valuation(
    company_id: int = Query(..., gt=0),
    warehouse_id: int | None = Query(default=None, gt=0),
    item_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    return inventory_costing_service.valuation(db, company_id, warehouse_id, item_id)
