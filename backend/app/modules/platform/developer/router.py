from fastapi import APIRouter,Depends,HTTPException,Header,BackgroundTasks
import secrets
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db,SessionLocal
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.platform.developer.models import DeveloperApp,DeveloperApiKey,DeveloperWebhook,DeveloperEvent,DeveloperWebhookDelivery,DeveloperCustomField
from app.modules.platform.developer.schemas import *
from app.modules.platform.developer.service import create_app,create_key,authenticate_key,sha,encrypt_secret,decrypt_secret,sign_webhook
router=APIRouter(prefix="/developer",tags=["Developer Platform"])
def company_ok(db,cid,user):
    if not user.tenant_id or not db.scalar(select(Company.id).where(Company.id==cid,Company.tenant_id==user.tenant_id)):raise HTTPException(404,"Company not found")
@router.post("/apps",response_model=AppCreated,status_code=201,dependencies=[Depends(require_permission("developer.manage"))])
def apps(p:AppCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user);a,s=create_app(db,user,p);return {**AppResponse.model_validate(a).model_dump(),"client_secret":s}
@router.get("/apps",response_model=list[AppResponse],dependencies=[Depends(require_permission("developer.access"))])
def list_apps(company_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,company_id,user);return list(db.scalars(select(DeveloperApp).where(DeveloperApp.company_id==company_id).order_by(DeveloperApp.id.desc())).all())
@router.post("/keys",response_model=KeyCreated,status_code=201,dependencies=[Depends(require_permission("developer.manage"))])
def keys(p:KeyCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    a=db.scalar(select(DeveloperApp).where(DeveloperApp.id==p.app_id,DeveloperApp.is_active.is_(True)))
    if not a:raise HTTPException(404,"App not found")
    company_ok(db,a.company_id,user)
    if not set(p.scopes).issubset(set(a.scopes)): raise HTTPException(422,"API key scopes must be a subset of app scopes")
    k,raw=create_key(db,p);return {"id":k.id,"key":raw,"key_prefix":k.key_prefix,"scopes":k.scopes,"expires_at":k.expires_at}
@router.delete("/keys/{key_id}",dependencies=[Depends(require_permission("developer.manage"))])
def revoke_key(key_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    k=db.get(DeveloperApiKey,key_id);a=db.get(DeveloperApp,k.app_id) if k else None
    if not k or not a:raise HTTPException(404,"Key not found")
    company_ok(db,a.company_id,user);k.revoked_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc);db.commit();return {"revoked":True}
@router.post("/webhooks",response_model=WebhookCreated,status_code=201,dependencies=[Depends(require_permission("developer.manage"))])
def webhook(p:WebhookCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    a=db.get(DeveloperApp,p.app_id)
    if not a:raise HTTPException(404,"App not found")
    company_ok(db,a.company_id,user);secret=secrets.token_urlsafe(32);w=DeveloperWebhook(app_id=a.id,url=p.url,secret_hash=sha(secret),secret_encrypted=encrypt_secret(secret),events=p.events);db.add(w);db.commit();db.refresh(w);return {**WebhookResponse.model_validate(w).model_dump(),"signing_secret":secret}
@router.get("/webhooks",response_model=list[WebhookResponse],dependencies=[Depends(require_permission("developer.access"))])
def webhooks(company_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,company_id,user);return list(db.scalars(select(DeveloperWebhook).join(DeveloperApp).where(DeveloperApp.company_id==company_id)).all())
@router.post("/events/publish",dependencies=[Depends(require_permission("developer.manage"))])
def publish(p:EventPublish,background:BackgroundTasks,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user)
    if db.scalar(select(DeveloperEvent).where(DeveloperEvent.company_id==p.company_id,DeveloperEvent.event_id==p.event_id)):return {"accepted":True,"duplicate":True}
    e=DeveloperEvent(**p.model_dump());db.add(e);db.flush();count=0
    hooks=list(db.scalars(select(DeveloperWebhook).join(DeveloperApp).where(DeveloperApp.company_id==p.company_id,DeveloperWebhook.is_active.is_(True))).all())
    for w in hooks:
        if w.events and p.event_type not in w.events and "*" not in w.events:continue
        db.add(DeveloperWebhookDelivery(webhook_id=w.id,event_id=p.event_id,event_type=p.event_type,payload=p.payload));count+=1
    db.commit()
    for d in db.scalars(select(DeveloperWebhookDelivery).where(DeveloperWebhookDelivery.event_id==p.event_id)).all(): background.add_task(_deliver,d.id)
    return {"accepted":True,"deliveries_created":count}
@router.get("/events/deliveries",dependencies=[Depends(require_permission("developer.access"))])
def deliveries(company_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,company_id,user);return [{"id":d.id,"event_id":d.event_id,"event_type":d.event_type,"status":d.status,"attempts":d.attempts,"response_code":d.response_code} for d in db.scalars(select(DeveloperWebhookDelivery).join(DeveloperWebhook).join(DeveloperApp).where(DeveloperApp.company_id==company_id).order_by(DeveloperWebhookDelivery.id.desc()).limit(200)).all()]
@router.post("/custom-fields",response_model=CustomFieldResponse,status_code=201,dependencies=[Depends(require_permission("developer.manage"))])
def custom_field(p:CustomFieldCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user);o=DeveloperCustomField(**p.model_dump());db.add(o);db.commit();db.refresh(o);return o
@router.get("/custom-fields",response_model=list[CustomFieldResponse],dependencies=[Depends(require_permission("developer.access"))])
def custom_fields(company_id:int,entity_type:str|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,company_id,user);q=select(DeveloperCustomField).where(DeveloperCustomField.company_id==company_id,DeveloperCustomField.is_active.is_(True))
    if entity_type:q=q.where(DeveloperCustomField.entity_type==entity_type)
    return list(db.scalars(q.order_by(DeveloperCustomField.id)).all())
@router.get("/v1/ping")
def api_ping(x_api_key:str|None=Header(default=None),db:Session=Depends(get_db)):
    if not x_api_key or not authenticate_key(db,x_api_key,"api:read"):raise HTTPException(401,"Invalid API key or scope")
    return {"ok":True,"api_version":"v1"}

def _deliver(delivery_id:int):
    import requests
    from datetime import datetime,timezone
    db=SessionLocal()
    try:
        d=db.get(DeveloperWebhookDelivery,delivery_id)
        if not d or d.status=="delivered":return
        w=db.get(DeveloperWebhook,d.webhook_id)
        if not w or not w.is_active:d.status="disabled";db.commit();return
        ts=int(datetime.now(timezone.utc).timestamp());body={"id":d.event_id,"type":d.event_type,"data":d.payload}
        try:
            r=requests.post(w.url,json=body,headers={"Content-Type":"application/json","X-PrimeERP-Event":d.event_type,"X-PrimeERP-Timestamp":str(ts),"X-PrimeERP-Signature":"sha256="+sign_webhook(decrypt_secret(w.secret_encrypted),ts,body)},timeout=10)
            d.attempts+=1;d.response_code=r.status_code;d.response_body=r.text[:4000]
            if 200<=r.status_code<300:d.status="delivered";d.delivered_at=datetime.now(timezone.utc)
            else:d.status="failed"
        except Exception as exc:
            d.attempts+=1;d.response_body=str(exc)[:4000];d.status="failed"
        db.commit()
    finally:db.close()

@router.post("/deliveries/{delivery_id}/retry",dependencies=[Depends(require_permission("developer.manage"))])
def retry_delivery(delivery_id:int,background:BackgroundTasks,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    d=db.get(DeveloperWebhookDelivery,delivery_id)
    if not d:raise HTTPException(404,"Delivery not found")
    w=db.get(DeveloperWebhook,d.webhook_id);a=db.get(DeveloperApp,w.app_id) if w else None
    if not a:raise HTTPException(404,"Webhook app not found")
    company_ok(db,a.company_id,user)
    if d.attempts>=5:raise HTTPException(409,"Delivery retry limit reached")
    background.add_task(_deliver,d.id)
    return {"queued":True,"delivery_id":d.id}
