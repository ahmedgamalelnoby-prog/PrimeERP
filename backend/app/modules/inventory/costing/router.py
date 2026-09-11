from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.inventory.costing.schemas import InventoryValuationResponse
from app.modules.inventory.costing.service import inventory_costing_service

router = APIRouter(prefix="/inventory/costing", tags=["Inventory Costing"])


@router.get(
    "/valuation",
    response_model=InventoryValuationResponse,
    dependencies=[Depends(require_permission("inventory.access"))],
)
def inventory_valuation(
    company_id: int = Query(..., gt=0),
    warehouse_id: int | None = Query(default=None, gt=0),
    item_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return inventory_costing_service.valuation(db, company_id, warehouse_id, item_id)
