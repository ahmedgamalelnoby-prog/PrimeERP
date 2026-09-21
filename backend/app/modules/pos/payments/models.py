from sqlalchemy import Column,DateTime,ForeignKey,Integer,Numeric,String
from sqlalchemy.sql import func
from app.database.base import Base
class POSPayment(Base):
    __tablename__="pos_payments"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); order_id=Column(Integer,ForeignKey("pos_orders.id",ondelete="CASCADE"),nullable=False); payment_method=Column(String(30),nullable=False); amount=Column(Numeric(18,2),nullable=False); reference=Column(String(150)); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
