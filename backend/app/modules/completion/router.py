from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from .service import completion_service
router=APIRouter(prefix="/completion",tags=["Enterprise Completion"])
@router.post("/periods/{company_id}/{period_key}/lock")
def lock_period(company_id:int,period_key:str,module:str="*",reason:str|None=None,db:Session=Depends(get_db)):
    return completion_service.lock_period(db,company_id,period_key,module,reason)
