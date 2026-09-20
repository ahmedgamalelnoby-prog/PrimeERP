import hashlib,secrets,base64,json,hmac,time
from datetime import datetime,timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from app.core.config import settings
from app.modules.platform.developer.models import DeveloperApp,DeveloperApiKey,DeveloperWebhook,DeveloperEvent,DeveloperWebhookDelivery,DeveloperCustomField

def sha(v:str)->str:return hashlib.sha256(v.encode()).hexdigest()
def _fernet(): return Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest()))
def encrypt_secret(v:str)->str:return _fernet().encrypt(v.encode()).decode()
def decrypt_secret(v:str)->str:return _fernet().decrypt(v.encode()).decode()
def create_app(db,user,p):
    client_id="app_"+secrets.token_urlsafe(18);secret=secrets.token_urlsafe(36)
    a=DeveloperApp(company_id=p.company_id,created_by=user.id,name=p.name,client_id=client_id,client_secret_hash=sha(secret),redirect_uris=p.redirect_uris,scopes=p.scopes);db.add(a);db.commit();db.refresh(a);return a,secret
def create_key(db,p):
    raw="pk_"+secrets.token_urlsafe(32);k=DeveloperApiKey(app_id=p.app_id,key_prefix=raw[:12],key_hash=sha(raw),scopes=p.scopes,expires_at=p.expires_at);db.add(k);db.commit();db.refresh(k);return k,raw
def authenticate_key(db,raw,required_scope=None):
    k=db.scalar(select(DeveloperApiKey).where(DeveloperApiKey.key_hash==sha(raw),DeveloperApiKey.revoked_at.is_(None)))
    if not k:return None
    if k.expires_at and k.expires_at<=datetime.now(timezone.utc):return None
    if required_scope and required_scope not in set(k.scopes or []):return None
    app=db.get(DeveloperApp,k.app_id)
    if not app or not app.is_active:return None
    k.last_used_at=datetime.now(timezone.utc);db.commit();return k
def sign_webhook(secret:str,timestamp:int,body:dict)->str:
    raw=f"{timestamp}.{json.dumps(body,separators=(',',':'),sort_keys=True)}".encode()
    return hmac.new(secret.encode(),raw,hashlib.sha256).hexdigest()
