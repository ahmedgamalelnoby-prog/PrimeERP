from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.catalog.service import catalog_service
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User

router=APIRouter(prefix="/manufacturing",tags=["Manufacturing"])

class MaterialIssue(BaseModel):
    company_id:int=Field(gt=0); item_id:int=Field(gt=0); source_location_id:int=Field(gt=0); quantity:Decimal=Field(gt=0); reference:str=Field(min_length=1,max_length=100)

def _company(db,cid,user):
    if user.tenant_id is None: raise HTTPException(403,"User is not assigned to a tenant")
    if db.scalar(select(Company).where(Company.id==cid,Company.tenant_id==user.tenant_id,Company.is_active.is_(True))) is None: raise HTTPException(403,"Company is outside the current tenant")

@router.get("/bom")
def list_bom(company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,company_id,current_user); return catalog_service.list_recipes(db,company_id)

@router.get("/bom/{recipe_id}")
def get_bom(recipe_id:int,company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,company_id,current_user); return catalog_service.get_recipe(db,company_id,recipe_id)

@router.post("/material-issues")
def issue_material(payload:MaterialIssue,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,payload.company_id,current_user)
    move=inventory_stock_move_service.create_draft(db,StockMoveCreate(company_id=payload.company_id,item_id=payload.item_id,source_location_id=payload.source_location_id,quantity=payload.quantity,unit_cost=0,movement_type="issue",reference=payload.reference,source_module="manufacturing",source_entity="material_issue",source_id=payload.reference))
    inventory_stock_move_service.post(db,tenant_id=current_user.tenant_id,company_id=payload.company_id,move_id=move.id,user_id=current_user.id)
    db.commit(); db.refresh(move); return move
