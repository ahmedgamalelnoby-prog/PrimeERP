from sqlalchemy import Column,Integer,Numeric,String,ForeignKey,DateTime,CheckConstraint,UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base
class CommerceBackorder(Base):
    __tablename__="commerce_backorders"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    source_kind=Column(String(10),nullable=False)
    source_document_id=Column(Integer,nullable=False,index=True)
    source_line_id=Column(Integer,nullable=False,index=True)
    quantity=Column(Numeric(18,4),nullable=False)
    fulfilled_quantity=Column(Numeric(18,4),nullable=False,default=0)
    status=Column(String(20),nullable=False,default="open")
    created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())
    __table_args__=(CheckConstraint("source_kind IN ('sale','purchase')",name="ck_backorder_kind"),CheckConstraint("quantity > 0",name="ck_backorder_qty"),CheckConstraint("fulfilled_quantity >= 0 AND fulfilled_quantity <= quantity",name="ck_backorder_fulfilled"),CheckConstraint("status IN ('open','fulfilled','cancelled')",name="ck_backorder_status"),UniqueConstraint("company_id","source_kind","source_line_id","status",name="uq_backorder_active_line"))