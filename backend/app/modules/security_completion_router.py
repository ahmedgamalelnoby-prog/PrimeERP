from datetime import datetime,timezone
from fastapi import APIRouter,Depends,Query,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select,update
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.identity.models.refresh_token import RefreshToken
from app.modules.completion.domain_models import APIClientCredential
from app.modules.completion.domain_service import domain_completion_service
from app.modules.audit.service import record_audit_event

router=APIRouter(prefix="/security",tags=["Security Completion"])
class APIKeyRotation(BaseModel):
    name:str|None=None
    scopes:list[str]=Field(default_factory=list)
    expires_at:datetime|None=None
@router.post("/sessions/revoke-all")
def revoke_sessions(db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    now=datetime.now(timezone.utc)
    count=db.query(RefreshToken).filter(RefreshToken.user_id==u.id,RefreshToken.revoked_at.is_(None),RefreshToken.is_active.is_(True)).update({RefreshToken.revoked_at:now,RefreshToken.is_active:False},synchronize_session=False)
    db.commit()
    record_audit_event(db,action="security.sessions_revoke_all",entity_type="user",entity_id=u.id,user_id=u.id,tenant_id=u.tenant_id,metadata={"revoked":count})
    db.commit()
    return {"revoked":count}
@router.post("/api-keys/{key_id}/rotate")
def rotate_api_key(key_id:int,p:APIKeyRotation,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    if u.tenant_id is None: raise HTTPException(403,"Tenant required")
    old=db.scalar(select(APIClientCredential).where(APIClientCredential.id==key_id,APIClientCredential.tenant_id==u.tenant_id).with_for_update())
    if old is None: raise HTTPException(404,"API key not found")
    old.is_active=False
    x,raw=domain_completion_service.api_key(db,u.tenant_id,old.company_id,p.name or old.name,p.scopes or __import__("json").loads(old.scopes or "[]"),p.expires_at)
    db.commit()
    record_audit_event(db,action="security.api_key_rotate",entity_type="api_key",entity_id=x.id,user_id=u.id,tenant_id=u.tenant_id,company_id=x.company_id,metadata={"replaced_key_id":old.id,"prefix":x.key_prefix})
    db.commit()
    return {"id":x.id,"key":raw,"prefix":x.key_prefix,"replaced_key_id":old.id,"expires_at":x.expires_at}
@router.post("/api-keys/{key_id}/revoke")
def revoke_api_key(key_id:int,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    if u.tenant_id is None: raise HTTPException(403,"Tenant required")
    x=db.scalar(select(APIClientCredential).where(APIClientCredential.id==key_id,APIClientCredential.tenant_id==u.tenant_id).with_for_update())
    if x is None: raise HTTPException(404,"API key not found")
    x.is_active=False;db.commit(); record_audit_event(db,action="security.api_key_revoke",entity_type="api_key",entity_id=x.id,user_id=u.id,tenant_id=u.tenant_id,company_id=x.company_id,metadata={"prefix":x.key_prefix}); db.commit(); return {"id":x.id,"status":"revoked"}
@router.get("/api-keys")
def list_api_keys(db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    if u.tenant_id is None: raise HTTPException(403,"Tenant required")
    rows=db.scalars(select(APIClientCredential).where(APIClientCredential.tenant_id==u.tenant_id).order_by(APIClientCredential.id.desc())).all()
    return [{"id":x.id,"name":x.name,"prefix":x.key_prefix,"scopes":x.scopes,"is_active":x.is_active,"expires_at":x.expires_at,"last_used_at":x.last_used_at} for x in rows]
