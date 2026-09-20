from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.models import User
from app.modules.ai_reporting.models import ReportDeliveryLog, ReportSchedule
from app.modules.ai_reporting.service import ai_analysis_service, report_delivery_service, rows_to_csv
router=APIRouter(prefix="/ai-reporting",tags=["ai-reporting"],dependencies=[Depends(require_permission("reports.view"))])
REPORT_CATALOG={"sales_performance":"Sales Performance","cash_position":"Cash Position","receivables_aging":"Receivables Aging","inventory_performance":"Inventory Performance","profitability":"Profitability / P&L","tax_compliance":"Tax & Compliance","management_summary":"AI Management Summary"}
class AnalysisRequest(BaseModel): report_name:str=Field(min_length=1,max_length=160); metrics:dict[str,Any]; instructions:str|None=Field(default=None,max_length=4000)
class ScheduleRequest(BaseModel):
    name:str=Field(min_length=1,max_length=160); report_key:str; frequency:str=Field(default="monthly",pattern="^(daily|weekly|monthly|quarterly|custom)$"); cron:str|None=None; timezone:str="Africa/Cairo"; channels:list[str]=Field(default_factory=lambda:["email"]); recipients:list[str]=Field(default_factory=list); filters:dict[str,Any]=Field(default_factory=dict); format:str=Field(default="csv",pattern="^(csv|json)$"); include_ai:bool=True; next_run_at:datetime|None=None
class RunRequest(BaseModel):
    report_key:str; title:str|None=None; rows:list[dict[str,Any]]=Field(default_factory=list); metrics:dict[str,Any]=Field(default_factory=dict); recipients:list[str]=Field(default_factory=list); channels:list[str]=Field(default_factory=lambda:["email"]); include_ai:bool=True
def _tenant_id(user:User)->int:
    try:return int(get_effective_tenant_id(user))
    except Exception as exc:raise HTTPException(403,"Authenticated user has no tenant context") from exc
@router.get("/catalog")
def catalog(current_user:User=Depends(get_current_user)): return {"success":True,"data":{"reports":[{"key":k,"name":v} for k,v in REPORT_CATALOG.items()]}}
@router.post("/analyze")
def analyze(request:AnalysisRequest,current_user:User=Depends(get_current_user)): return {"success":True,"data":ai_analysis_service.analyze(request.report_name,request.metrics,request.instructions)}
@router.post("/schedules")
def create_schedule(request:ScheduleRequest,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if request.report_key not in REPORT_CATALOG: raise HTTPException(400,"Unknown report_key")
    if set(request.channels)-{"email","whatsapp"}: raise HTTPException(400,"Supported channels are email and whatsapp")
    if not request.recipients: raise HTTPException(400,"At least one recipient is required")
    s=ReportSchedule(tenant_id=_tenant_id(current_user),name=request.name,report_key=request.report_key,frequency=request.frequency,cron=request.cron,timezone=request.timezone,channels=json.dumps(request.channels),recipients=json.dumps(request.recipients),filters=json.dumps(request.filters,ensure_ascii=False),format=request.format,include_ai=request.include_ai,next_run_at=request.next_run_at)
    db.add(s); db.commit(); db.refresh(s); return {"success":True,"data":{"id":s.id,"name":s.name,"status":"active"}}
@router.get("/schedules")
def list_schedules(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    tid=_tenant_id(current_user); rows=db.query(ReportSchedule).filter(ReportSchedule.tenant_id==tid).order_by(ReportSchedule.id.desc()).all()
    return {"success":True,"data":{"schedules":[{"id":s.id,"name":s.name,"report_key":s.report_key,"frequency":s.frequency,"channels":json.loads(s.channels or "[]"),"recipients":json.loads(s.recipients or "[]"),"include_ai":s.include_ai,"is_active":s.is_active,"next_run_at":s.next_run_at.isoformat() if s.next_run_at else None} for s in rows]}}
@router.post("/run")
def run_report(request:RunRequest,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if request.report_key not in REPORT_CATALOG: raise HTTPException(400,"Unknown report_key")
    if not request.recipients: raise HTTPException(400,"At least one recipient is required")
    if set(request.channels)-{"email","whatsapp"}: raise HTTPException(400,"Supported channels are email and whatsapp")
    tid=_tenant_id(current_user); title=request.title or REPORT_CATALOG[request.report_key]; analysis=ai_analysis_service.analyze(title,request.metrics) if request.include_ai else None; body=f"PrimeERP Report: {title}\n\n{analysis.get('summary','') if analysis else ''}".strip(); attachment=(f"{request.report_key}.csv",rows_to_csv(request.rows),"text/csv") if request.rows else None
    results=[]
    for channel in request.channels:
        for recipient in request.recipients:
            result=report_delivery_service.send_email(recipient,f"PrimeERP - {title}",body,attachment) if channel=="email" else report_delivery_service.send_whatsapp(recipient,body)
            db.add(ReportDeliveryLog(tenant_id=tid,report_key=request.report_key,channel=channel,recipient=recipient,status="sent" if result.ok else "failed",provider_message_id=result.message_id,error=result.error))
            results.append({"channel":channel,"recipient":recipient,"ok":result.ok,"message_id":result.message_id,"error":result.error})
    db.commit(); return {"success":all(x["ok"] for x in results),"data":{"report_key":request.report_key,"generated_at":datetime.now(timezone.utc).isoformat(),"analysis":analysis,"deliveries":results}}
@router.get("/deliveries")
def delivery_logs(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    tid=_tenant_id(current_user); logs=db.query(ReportDeliveryLog).filter(ReportDeliveryLog.tenant_id==tid).order_by(ReportDeliveryLog.id.desc()).limit(100).all()
    return {"success":True,"data":{"deliveries":[{"id":x.id,"report_key":x.report_key,"channel":x.channel,"recipient":x.recipient,"status":x.status,"error":x.error} for x in logs]}}
