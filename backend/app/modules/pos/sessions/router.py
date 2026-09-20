from decimal import Decimal
from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.pos.sessions.service import pos_session_service

router=APIRouter(
    prefix="/pos/sessions",
    tags=["POS Sessions"],
    dependencies=[Depends(require_permission("commerce.access"))],
)

class OpenPayload(BaseModel):
    company_id:int=Field(gt=0)
    terminal_id:int=Field(gt=0)
    opening_cash:Decimal=Field(default=0,ge=0)
    notes:str|None=None

class ClosePayload(BaseModel):
    company_id:int=Field(gt=0)
    actual_cash:Decimal=Field(ge=0)
    notes:str|None=None

@router.get("")
def list_sessions(
    company_id:int=Query(...,gt=0),
    terminal_id:int|None=Query(None,gt=0),
    u:User=Depends(get_current_user),
    db:Session=Depends(get_db),
):
    return pos_session_service.list(db,u.tenant_id,company_id,terminal_id)

@router.post("/open",status_code=201,dependencies=[Depends(require_permission("commerce.write"))])
def open_session(
    p:OpenPayload,
    u:User=Depends(get_current_user),
    db:Session=Depends(get_db),
):
    x=pos_session_service.open(db,u.tenant_id,p.company_id,p.terminal_id,u.id,p.opening_cash,p.notes)
    db.commit()
    db.refresh(x)
    return x

@router.post("/{session_id}/close",dependencies=[Depends(require_permission("commerce.write"))])
def close_session(
    session_id:int,
    p:ClosePayload,
    u:User=Depends(get_current_user),
    db:Session=Depends(get_db),
):
    x=pos_session_service.close(db,u.tenant_id,p.company_id,session_id,p.actual_cash,u.id,p.notes)
    db.commit()
    db.refresh(x)
    return x
