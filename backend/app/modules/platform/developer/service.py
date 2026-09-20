import hashlib,secrets
from datetime import datetime,timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.platform.developer.models import DeveloperApp,DeveloperApiKey,DeveloperWebhook,DeveloperEvent,DeveloperWebhookDelivery,DeveloperCustomField

def sha(v:str)->str:return hashlib.sha256(v.encode()).hexdigest()
def create_app(db,user,p):
    client_id="app_"+secrets.token_urlsafe(18);secret=secrets.token_urlsafe(36)
    a=DeveloperApp(company_id=p.company_id,created_by=user.id,name=p.name,client_id=client_id,client_secret_hash=sha(secret),redirect_uris=p.redirect_uris,scopes=p.scopes);db.add(a);db.commit();db.refresh(a);return a,secret
def create_key(db,p):
    raw="pk_"+secrets.token_urlsafe(32);k=DeveloperApiKey(app_id=p.app_id,key_prefix=raw[:12],key_hash=sha(raw),scopes=p.scopes,expires_at=p.expires_at);db.add(k);db.commit();db.refresh(k);return k,raw
def authenticate_key(db,raw):
    k=db.scalar(select(DeveloperApiKey).where(DeveloperApiKey.key_hash==sha(raw),DeveloperApiKey.revoked_at.is_(None)))
    if not k:return None
    if k.expires_at and k.expires_at<=datetime.now(timezone.utc):return None
    k.last_used_at=datetime.now(timezone.utc);db.commit();return k
