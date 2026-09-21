from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

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
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(status_code=403, detail="Company is outside the current tenant")
    return company


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


from app.modules.inventory.costing.variance_service import inventory_cost_variance_service

@router.post("/variance", dependencies=[Depends(require_permission("inventory.post"))])
def calculate_cost_variance(company_id:int=Query(...,gt=0), item_id:int=Query(...,gt=0), warehouse_id:int=Query(...,gt=0), variant_id:int|None=Query(default=None,gt=0), db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        row=inventory_cost_variance_service.calculate(db, company_id=company_id,item_id=item_id,warehouse_id=warehouse_id,variant_id=variant_id,user_id=current_user.id)
        db.commit(); db.refresh(row); return row
    except ValueError as exc:
        db.rollback(); raise HTTPException(422,str(exc))

@router.get("/variance")
def list_cost_variances(company_id:int=Query(...,gt=0), item_id:int|None=Query(default=None,gt=0), db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    return inventory_cost_variance_service.list(db, company_id, item_id)
