from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from .schemas import PropertyCreate,UnitCreate,TenantCreate,ContractCreate,ChargeCreate,ChargeRead
from .service import rental_service

router=APIRouter(prefix="/rentals",tags=["Rentals"])

@router.post("/properties")
def create_property(payload:PropertyCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return rental_service.create_property(db,current_user.tenant_id,current_user.company_id,payload)

@router.post("/units")
def create_unit(payload:UnitCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return rental_service.create_unit(db,current_user.tenant_id,current_user.company_id,payload)

@router.post("/tenants")
def create_tenant(payload:TenantCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return rental_service.create_tenant(db,current_user.tenant_id,current_user.company_id,payload)

@router.post("/contracts")
def create_contract(payload:ContractCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return rental_service.create_contract(db,current_user.tenant_id,current_user.company_id,payload)

@router.get("/contracts")
def list_contracts(db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return rental_service.list_contracts(db,current_user.tenant_id,current_user.company_id)

@router.post("/charges",response_model=ChargeRead)
def generate_charge(payload:ChargeCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return rental_service.generate_charge(db,current_user.tenant_id,current_user.company_id,payload)
