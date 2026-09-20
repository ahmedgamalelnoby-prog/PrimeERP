from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import require_permission
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.treasury.completion_models import TreasuryTransaction
from app.modules.treasury.schemas_completion import TreasuryTransactionCreate,TreasuryApproval,TreasuryDailyCloseCreate,TreasuryForecastCreate,TreasuryTransactionResponse
from app.modules.treasury.completion_service import create_transaction,decide,daily_close,forecast,positions,list_transactions,reverse_transaction,_company
router=APIRouter(prefix="/treasury/core",tags=["Treasury Core"],dependencies=[Depends(require_permission("treasury.access"))])
@router.get("/transactions",response_model=list[TreasuryTransactionResponse])
def list_all(company_id:int=Query(...,gt=0),status:str|None=None,transaction_type:str|None=None,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 return list_transactions(db,company_id,current_user,status,transaction_type)

@router.post("/transactions",response_model=TreasuryTransactionResponse,dependencies=[Depends(require_permission("treasury.write"))])
def create(p:TreasuryTransactionCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=create_transaction(db,p,current_user);db.commit();db.refresh(o);return o
@router.post("/transactions/{tx_id}/reverse",response_model=TreasuryTransactionResponse,dependencies=[Depends(require_permission("treasury.post"))])
def reverse(tx_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=db.get(TreasuryTransaction,tx_id)
 if o is None: raise HTTPException(404,"Treasury transaction not found")
 _company(db,o.company_id,current_user)
 try:
  obj=reverse_transaction(db,o,current_user);db.commit();db.refresh(obj);return obj
 except (HTTPException,ValueError): db.rollback(); raise

@router.post("/transactions/{tx_id}/decision",response_model=TreasuryTransactionResponse,dependencies=[Depends(require_permission("treasury.post"))])
def decision(tx_id:int,p:TreasuryApproval,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=db.get(TreasuryTransaction,tx_id)
 if o is None: raise HTTPException(404,"Treasury transaction not found")
 _company(db,o.company_id,current_user)
 o=decide(db,o,p.approve,current_user);db.commit();db.refresh(o);return o
@router.post("/daily-closing",dependencies=[Depends(require_permission("treasury.post"))])
def close(p:TreasuryDailyCloseCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=daily_close(db,p,current_user);db.commit();db.refresh(o);return o
@router.post("/forecast",dependencies=[Depends(require_permission("treasury.write"))])
def make_forecast(p:TreasuryForecastCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=forecast(db,p,current_user);db.commit();db.refresh(o);return o
@router.get("/positions",dependencies=[Depends(require_permission("treasury.access"))])
def get_positions(company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):return positions(db,company_id,current_user)
