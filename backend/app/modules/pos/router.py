from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.pos.schemas import OutletCreate,DeviceCreate,SessionOpen,OrderCreate,PaymentCreate,SessionClose
from app.modules.commerce.accounting_models import POSPaymentAccountMapping
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.companies.models import Company
from app.modules.pos.service import pos_service
router=APIRouter(prefix="/pos",tags=["POS"],dependencies=[Depends(require_permission("commerce.access"))])
def run(fn):
    try:return fn()
    except ValueError as e:raise HTTPException(400,str(e))

@router.put("/payment-account-mappings/{method}")
def set_payment_account_mapping(method: str, company_id: int, account_combination_id: int, user: User=Depends(get_current_user), db=Depends(get_db)):
    if method not in {"cash","card","bank","other"}:
        raise HTTPException(400, "Unsupported payment method")
    company = db.scalar(select(Company).where(Company.id==company_id, Company.tenant_id==user.tenant_id))
    account = db.scalar(select(AccountCombination).where(AccountCombination.id==account_combination_id, AccountCombination.company_id==company_id))
    if not company or not account:
        raise HTTPException(403, "Company or account is outside the current tenant")
    mapping = db.scalar(select(POSPaymentAccountMapping).where(POSPaymentAccountMapping.company_id==company_id, POSPaymentAccountMapping.method==method))
    if mapping is None:
        mapping = POSPaymentAccountMapping(company_id=company_id, method=method, account_combination_id=account_combination_id)
        db.add(mapping)
    else:
        mapping.account_combination_id = account_combination_id
    db.commit(); db.refresh(mapping); return mapping

@router.get("/payment-account-mappings")
def list_payment_account_mappings(company_id: int, user: User=Depends(get_current_user), db=Depends(get_db)):
    if not db.scalar(select(Company).where(Company.id==company_id, Company.tenant_id==user.tenant_id)):
        raise HTTPException(403, "Company is outside the current tenant")
    return list(db.scalars(select(POSPaymentAccountMapping).where(POSPaymentAccountMapping.company_id==company_id).order_by(POSPaymentAccountMapping.method)).all())

@router.post("/outlets")
def outlet(p:OutletCreate,user:User=Depends(get_current_user),db=Depends(get_db)):
    o=run(lambda:pos_service.create_outlet(db,p,user));db.commit();db.refresh(o);return o
@router.post("/devices")
def device(p:DeviceCreate,user:User=Depends(get_current_user),db=Depends(get_db)):
    d=run(lambda:pos_service.create_device(db,p,user));db.commit();db.refresh(d);return d
@router.post("/sessions/open")
def open_session(p:SessionOpen,user:User=Depends(get_current_user),db=Depends(get_db)):
    s=run(lambda:pos_service.open_session(db,p,user));db.commit();db.refresh(s);return s
@router.post("/orders")
def order(p:OrderCreate,user:User=Depends(get_current_user),db=Depends(get_db)):
    o=run(lambda:pos_service.create_order(db,p,user));db.commit();db.refresh(o);return o
@router.post("/orders/{order_id}/finalize")
def finalize(order_id:int,company_id:int,user:User=Depends(get_current_user),db=Depends(get_db)):
    o=run(lambda:pos_service.finalize(db,company_id,order_id,user));db.commit();db.refresh(o);return o
@router.post("/payments")
def payment(p:PaymentCreate,user:User=Depends(get_current_user),db=Depends(get_db)):
    x=run(lambda:pos_service.pay(db,p,user));db.commit();db.refresh(x);return x
@router.post("/sessions/{session_id}/close")
def close(session_id:int,p:SessionClose,user:User=Depends(get_current_user),db=Depends(get_db)):
    s=run(lambda:pos_service.close_session(db,p.company_id,session_id,p.closing_total,user,p.closing_cash,p.closing_card,p.closing_bank,p.closing_other));db.commit();db.refresh(s);return s
