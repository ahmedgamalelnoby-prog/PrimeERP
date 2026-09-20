from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import require_permission
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.treasury.completion_models import TreasuryTransaction
from app.modules.treasury.schemas_completion import TreasuryTransactionCreate,TreasuryApproval,TreasuryDailyCloseCreate,TreasuryForecastCreate,TreasuryTransactionResponse
from app.modules.treasury.completion_service import create_transaction,decide,daily_close,forecast,positions
router=APIRouter(prefix="/treasury/core",tags=["Treasury Core"],dependencies=[Depends(require_permission("treasury.access"))])
@router.post("/transactions",response_model=TreasuryTransactionResponse,dependencies=[Depends(require_permission("treasury.write"))])
def create(p:TreasuryTransactionCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=create_transaction(db,p,current_user);db.commit();db.refresh(o);return o
@router.post("/transactions/{tx_id}/decision",response_model=TreasuryTransactionResponse,dependencies=[Depends(require_permission("treasury.post"))])
def decision(tx_id:int,p:TreasuryApproval,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=db.get(TreasuryTransaction,tx_id)
 if o is None or o.company_id!=current_user.company_id:raise HTTPException(404,"Treasury transaction not found")
 o=decide(db,o,p.approve,current_user);db.commit();db.refresh(o);return o
@router.post("/daily-closing",dependencies=[Depends(require_permission("treasury.post"))])
def close(p:TreasuryDailyCloseCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=daily_close(db,p,current_user);db.commit();db.refresh(o);return o
@router.post("/forecast")
def make_forecast(p:TreasuryForecastCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 o=forecast(db,p,current_user);db.commit();db.refresh(o);return o
@router.get("/positions")
def get_positions(company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):return positions(db,company_id,current_user)
