from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .finance_models import SettlementAllocation,ReturnControl,IntegrationDelivery
class FinanceCompletionService:
 def allocate(self,db,**kw):
  if kw["amount"]<=0:raise HTTPException(422,"Allocation amount must be positive")
  x=SettlementAllocation(**kw);db.add(x);db.flush();return x
 def return_control(self,db,**kw):
  x=ReturnControl(**kw);db.add(x);db.flush();return x
 def advance_return(self,db,x,status):
  order=["requested","approved","inspected","restocked","refunded","reversed"]
  if status not in order or order.index(status)<order.index(x.status):raise HTTPException(409,"Return status cannot move backwards")
  x.status=status
  if status=="approved":x.approved=True
  elif status=="inspected":x.inspected=True
  elif status=="restocked":x.restocked=True
  elif status=="refunded":x.refunded=True
  elif status=="reversed":x.reversed=True
  db.flush();return x
 def delivery_failure(self,db,x,error):
  x.attempts+=1;x.last_error=error
  if x.attempts>=x.max_attempts:x.dead_letter=True;x.status="dead_letter"
  else:x.status="retry"
  db.flush();return x
 def replay(self,db,x):
  if not x.dead_letter:raise HTTPException(409,"Only dead-letter deliveries can be replayed")
  x.dead_letter=False;x.status="pending";x.replayed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc);db.flush();return x
finance_completion_service=FinanceCompletionService()
