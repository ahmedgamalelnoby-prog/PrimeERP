from decimal import Decimal
from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.modules.pos.sessions.models import POSSession
from app.modules.restaurant.models import PosTerminal
from app.modules.companies.models import Company
from app.modules.commerce.models import SalesDocument, CommercePayment
class POSSessionService:
 def scope(self,db,company_id,tenant_id,terminal_id):
  if db.scalar(select(Company.id).where(Company.id==company_id,Company.tenant_id==tenant_id,Company.is_active.is_(True))) is None or db.scalar(select(PosTerminal.id).where(PosTerminal.id==terminal_id,PosTerminal.company_id==company_id,PosTerminal.is_active.is_(True))) is None: raise HTTPException(403,"Invalid company or terminal")
 def open(self,db,tenant_id,company_id,terminal_id,cashier_id,opening_cash,notes=None):
  self.scope(db,company_id,tenant_id,terminal_id);x=db.scalar(select(POSSession).where(POSSession.company_id==company_id,POSSession.terminal_id==terminal_id,POSSession.status.in_(["open","closing"])).with_for_update())
  if x: raise HTTPException(409,"Terminal already has an open session")
  x=POSSession(tenant_id=tenant_id,company_id=company_id,terminal_id=terminal_id,cashier_id=cashier_id,opening_cash=opening_cash,expected_cash=opening_cash,notes=notes);db.add(x);db.flush();return x
 def close(self,db,tenant_id,company_id,session_id,actual_cash,cashier_id,notes=None):
  x=db.scalar(select(POSSession).where(POSSession.id==session_id,POSSession.tenant_id==tenant_id,POSSession.company_id==company_id).with_for_update())
  if x is None: raise HTTPException(404,"POS session not found")
  if x.status!="open": raise HTTPException(409,"Only open sessions can be closed")
  if x.cashier_id != cashier_id: raise HTTPException(403,"Only the cashier assigned to this POS session can close it")
  cash_total=db.scalar(select(func.coalesce(func.sum(CommercePayment.amount),0)).join(SalesDocument, SalesDocument.id==CommercePayment.document_id).where(
   CommercePayment.company_id==company_id,
   CommercePayment.document_kind=="sale",
   CommercePayment.method=="cash",
   CommercePayment.status=="posted",
   SalesDocument.company_id==company_id,
   SalesDocument.pos_session_id==x.id,
  )) or 0
  x.expected_cash=Decimal(x.opening_cash or 0)+Decimal(cash_total)
  x.status="closed";x.closed_at=datetime.now(timezone.utc);x.actual_cash=actual_cash;x.difference=Decimal(actual_cash)-Decimal(x.expected_cash or 0);x.notes=notes or x.notes;db.flush();return x
 def list(self,db,tenant_id,company_id,terminal_id=None):
  q=select(POSSession).where(POSSession.tenant_id==tenant_id,POSSession.company_id==company_id)
  if terminal_id:q=q.where(POSSession.terminal_id==terminal_id)
  return list(db.scalars(q.order_by(POSSession.id.desc()).limit(200)).all())
pos_session_service=POSSessionService()