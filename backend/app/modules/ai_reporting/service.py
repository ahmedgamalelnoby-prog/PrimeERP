from __future__ import annotations
import csv, io, json, os, smtplib, ssl, urllib.error, urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any

@dataclass(frozen=True)
class DeliveryResult:
    ok: bool
    message_id: str | None = None
    error: str | None = None

class AIAnalysisService:
    def analyze(self, report_name: str, metrics: dict[str, Any], instructions: str | None = None) -> dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("AI_MODEL", "gpt-5.6-luna")
        if not api_key:
            return {"provider":"disabled","model":model,"summary":"AI provider is not configured.","insights":[],"recommendations":[]}
        body=json.dumps({"model":model,"input":[
            {"role":"system","content":"You are PrimeERP Management Intelligence. Analyze only supplied ERP metrics. Do not claim to have changed ERP data."},
            {"role":"user","content":json.dumps({"report":report_name,"metrics":metrics,"instructions":instructions or "Identify trends, anomalies, risks and concrete actions without inventing data."},ensure_ascii=False)}
        ]}).encode()
        req=urllib.request.Request("https://api.openai.com/v1/responses",data=body,headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=60) as response: payload=json.loads(response.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            return {"provider":"openai","model":model,"error":str(exc)}
        text=payload.get("output_text") or "\n".join(c.get("text","") for i in payload.get("output",[]) for c in i.get("content",[]) if c.get("type") in {"output_text","text"}).strip()
        return {"provider":"openai","model":model,"summary":text or "No analysis returned."}

class ReportDeliveryService:
    def send_email(self, recipient:str, subject:str, body:str, attachment:tuple[str,bytes,str]|None=None)->DeliveryResult:
        host=os.getenv("SMTP_HOST"); port=int(os.getenv("SMTP_PORT","587")); username=os.getenv("SMTP_USERNAME"); password=os.getenv("SMTP_PASSWORD"); sender=os.getenv("SMTP_FROM") or username
        if not host or not sender: return DeliveryResult(False,error="SMTP_HOST and SMTP_FROM/SMTP_USERNAME are required")
        msg=EmailMessage(); msg["From"]=sender; msg["To"]=recipient; msg["Subject"]=subject; msg.set_content(body)
        if attachment:
            filename,content,mime=attachment; maintype,subtype=mime.split("/",1); msg.add_attachment(content,maintype=maintype,subtype=subtype,filename=filename)
        try:
            with smtplib.SMTP(host,port,timeout=30) as smtp:
                if os.getenv("SMTP_STARTTLS","true").lower()=="true": smtp.starttls(context=ssl.create_default_context())
                if username: smtp.login(username,password or "")
                smtp.send_message(msg)
            return DeliveryResult(True)
        except (OSError,smtplib.SMTPException) as exc: return DeliveryResult(False,error=str(exc))
    def send_whatsapp(self, recipient:str, message:str)->DeliveryResult:
        token=os.getenv("WHATSAPP_ACCESS_TOKEN"); phone_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID"); version=os.getenv("WHATSAPP_GRAPH_VERSION","v23.0")
        if not token or not phone_id: return DeliveryResult(False,error="WhatsApp provider is not configured")
        payload=json.dumps({"messaging_product":"whatsapp","to":recipient,"type":"text","text":{"preview_url":False,"body":message[:4096]}}).encode()
        req=urllib.request.Request(f"https://graph.facebook.com/{version}/{phone_id}/messages",data=payload,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=30) as response: data=json.loads(response.read().decode())
            return DeliveryResult(True,message_id=((data.get("messages") or [{}])[0]).get("id"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc: return DeliveryResult(False,error=str(exc))
def rows_to_csv(rows:list[dict[str,Any]])->bytes:
    if not rows: return b""
    out=io.StringIO(); fields=list(dict.fromkeys(k for row in rows for k in row)); w=csv.DictWriter(out,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows); return out.getvalue().encode("utf-8-sig")
ai_analysis_service=AIAnalysisService(); report_delivery_service=ReportDeliveryService()
