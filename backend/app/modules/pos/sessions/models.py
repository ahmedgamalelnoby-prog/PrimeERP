from sqlalchemy import Column,DateTime,ForeignKey,Integer,Numeric,String
from sqlalchemy.sql import func
from app.database.base import Base
class POSSession(Base):
    __tablename__="pos_sessions"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); terminal_id=Column(Integer,ForeignKey("pos_terminals.id",ondelete="RESTRICT"),nullable=False); opened_by=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False); closed_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL")); opened_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False); closed_at=Column(DateTime(timezone=True)); opening_cash=Column(Numeric(18,2),nullable=False,default=0); closing_cash=Column(Numeric(18,2)); status=Column(String(20),nullable=False,default="open")
