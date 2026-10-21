from sqlalchemy import Boolean,Column,ForeignKey,Integer,String,UniqueConstraint
from app.database.base import Base
class POSTerminal(Base):
    __tablename__="pos_terminals"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); outlet_id=Column(Integer,ForeignKey("pos_outlets.id",ondelete="CASCADE"),nullable=False); code=Column(String(50),nullable=False); name=Column(String(150),nullable=False); is_active=Column(Boolean,nullable=False,default=True)
    __table_args__=(UniqueConstraint("outlet_id","code",name="uq_pos_terminals_outlet_code"),)
