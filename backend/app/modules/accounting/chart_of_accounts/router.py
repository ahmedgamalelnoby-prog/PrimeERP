from typing import Optional
from fastapi import APIRouter,Depends,Query,status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.accounting.chart_of_accounts.schemas import *
from app.modules.accounting.chart_of_accounts.service import chart_service
router=APIRouter()
@router.get("/departments",response_model=list[DepartmentResponse])
def departments(company_id:int=Query(gt=0),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return chart_service.departments(db,current_user,company_id)
@router.post("/departments",response_model=DepartmentResponse,status_code=status.HTTP_201_CREATED)
def create_department(payload:DepartmentCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return chart_service.create_department(db,payload,current_user)
@router.get("/cost-centers",response_model=list[CostCenterResponse])
def cost_centers(company_id:int=Query(gt=0),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return chart_service.cost_centers(db,current_user,company_id)
@router.post("/cost-centers",response_model=CostCenterResponse,status_code=status.HTTP_201_CREATED)
def create_cost_center(payload:CostCenterCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return chart_service.create_cost_center(db,payload,current_user)
@router.get("/natural-accounts",response_model=list[NaturalAccountResponse])
def natural_accounts(company_id:int=Query(gt=0),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return chart_service.natural_accounts(db,current_user,company_id)
@router.post("/natural-accounts",response_model=NaturalAccountResponse,status_code=status.HTTP_201_CREATED)
def create_natural_account(payload:NaturalAccountCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return chart_service.create_natural_account(db,payload,current_user)
@router.get("/combinations",response_model=list[AccountCombinationResponse])
def combinations(company_id:int=Query(gt=0),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return chart_service.combinations(db,current_user,company_id)
@router.post("/combinations",response_model=AccountCombinationResponse,status_code=status.HTTP_201_CREATED)
def create_combination(payload:AccountCombinationCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return chart_service.create_combination(db,payload,current_user)
