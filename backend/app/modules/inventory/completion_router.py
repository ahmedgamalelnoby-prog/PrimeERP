from fastapi import APIRouter,Depends,Query,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.manufacturing.completion_models import InventoryStockPolicy,InventoryCostReconciliation
from app.modules.inventory.items.models import InventoryStock
from app.modules.catalog.models import ProductCostHistory
from app.modules.inventory.stock_moves.models import InventoryCostLayer

router=APIRouter(prefix="/inventory/completion",tags=["Inventory Completion"])
def company(db,cid,u):
    if u.tenant_id is None: raise HTTPException(403,"Tenant required")
    x=db.scalar(select(Company).where(Company.id==cid,Company.tenant_id==u.tenant_id,Company.is_active.is_(True)))
    if x is None: raise HTTPException(403,"Company is outside the current tenant")
class Policy(BaseModel):
    warehouse_id:int|None=None
    allow_negative:bool=False
    warning_threshold:float=Field(default=0,ge=0)
    costing_method:str="weighted_average"
@router.put("/stock-policy")
def set_policy(p:Policy,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u)
    q=select(InventoryStockPolicy).where(InventoryStockPolicy.company_id==company_id,InventoryStockPolicy.warehouse_id==p.warehouse_id,InventoryStockPolicy.is_active.is_(True))
    x=db.scalar(q)
    if x is None:x=InventoryStockPolicy(company_id=company_id,**p.model_dump());db.add(x)
    else:
        for k,v in p.model_dump().items():setattr(x,k,v)
    db.commit();db.refresh(x);return x
@router.get("/stock-policy")
def get_policy(company_id:int=Query(...,gt=0),warehouse_id:int|None=None,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);x=db.scalar(select(InventoryStockPolicy).where(InventoryStockPolicy.company_id==company_id,InventoryStockPolicy.warehouse_id==warehouse_id,InventoryStockPolicy.is_active.is_(True)));return x
@router.post("/cost-reconciliation")
def reconcile(company_id:int=Query(...,gt=0),warehouse_id:int=Query(...,gt=0),item_id:int=Query(...,gt=0),method:str="weighted_average",db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u)
    stock=db.scalar(select(InventoryStock).where(InventoryStock.company_id==company_id,InventoryStock.warehouse_id==warehouse_id,InventoryStock.item_id==item_id).with_for_update())
    if stock is None: raise HTTPException(404,"Inventory stock not found")
    qty=__import__("decimal").Decimal(str(stock.quantity_on_hand or 0));sub=qty*__import__("decimal").Decimal(str(stock.average_cost or 0))
    method=method.lower()
    if method not in {"standard","weighted_average","fifo","actual"}: raise HTTPException(422,"Unsupported costing method")
    if method == "weighted_average": value=sub
    elif method == "fifo":
        layers=db.scalars(select(InventoryCostLayer).where(InventoryCostLayer.company_id==company_id,InventoryCostLayer.item_id==item_id,InventoryCostLayer.warehouse_id==warehouse_id,InventoryCostLayer.quantity_remaining>0).order_by(InventoryCostLayer.id)).all()
        value=sum((__import__("decimal").Decimal(x.quantity_remaining)*__import__("decimal").Decimal(x.unit_cost) for x in layers),__import__("decimal").Decimal("0"))
    else:
        hist=db.scalar(select(ProductCostHistory).where(ProductCostHistory.company_id==company_id,ProductCostHistory.product_id==item_id).order_by(ProductCostHistory.effective_at.desc(),ProductCostHistory.id.desc()))
        unit=__import__("decimal").Decimal(str(hist.cost)) if hist else __import__("decimal").Decimal(str(stock.average_cost or 0))
        value=qty*unit
    diff=value-sub
    x=InventoryCostReconciliation(company_id=company_id,item_id=item_id,warehouse_id=warehouse_id,method=method,quantity=qty,subledger_value=sub,recomputed_value=value,difference=diff,status="matched" if diff==0 else "variance")
    db.add(x);db.commit();db.refresh(x);return x
