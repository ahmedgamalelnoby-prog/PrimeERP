from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from .schemas import PropertyCreate,UnitCreate,TenantCreate,ContractCreate,ChargeCreate,ChargeRead
from .service import rental_service
router=APIRouter(prefix="/rentals",tags=["Rentals"],dependencies=[Depends(require_module("rentals"))])
@router.post("/properties")
def create_property(payload:PropertyCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    obj=rental_service.create_property(db,current_user.tenant_id,current_user.company_id,payload);db.commit();db.refresh(obj);return obj
@router.post("/units")
def create_unit(payload:UnitCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    obj=rental_service.create_unit(db,current_user.tenant_id,current_user.company_id,payload);db.commit();db.refresh(obj);return obj
@router.post("/tenants")
def create_tenant(payload:TenantCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    obj=rental_service.create_tenant(db,current_user.tenant_id,current_user.company_id,payload);db.commit();db.refresh(obj);return obj
@router.post("/contracts")
def create_contract(payload:ContractCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    obj=rental_service.create_contract(db,current_user.tenant_id,current_user.company_id,payload);db.commit();db.refresh(obj);return obj
@router.post("/contracts/{contract_id}/activate")
def activate_contract(contract_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    obj=rental_service.activate_contract(db,current_user.tenant_id,current_user.company_id,contract_id);db.commit();db.refresh(obj);return obj
@router.post("/contracts/{contract_id}/terminate")
def terminate_contract(contract_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    obj=rental_service.terminate_contract(db,current_user.tenant_id,current_user.company_id,contract_id);db.commit();db.refresh(obj);return obj
@router.get("/contracts")
def list_contracts(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return rental_service.list_contracts(db,current_user.tenant_id,current_user.company_id)
@router.get("/charges",response_model=list[ChargeRead])
def list_charges(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return rental_service.list_charges(db,current_user.tenant_id,current_user.company_id)
@router.post("/charges",response_model=ChargeRead)
def generate_charge(payload:ChargeCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    obj=rental_service.generate_charge(db,current_user.tenant_id,current_user.company_id,payload,current_user.id);db.commit();db.refresh(obj);return obj
