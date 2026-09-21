from sqlalchemy import Column,DateTime,ForeignKey,Integer,Numeric,String,UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base
class POSOrder(Base):
    __tablename__="pos_orders"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); outlet_id=Column(Integer,ForeignKey("pos_outlets.id",ondelete="RESTRICT"),nullable=False); terminal_id=Column(Integer,ForeignKey("pos_terminals.id",ondelete="RESTRICT"),nullable=False); session_id=Column(Integer,ForeignKey("pos_sessions.id",ondelete="RESTRICT"),nullable=False); order_number=Column(String(80),nullable=False); status=Column(String(30),nullable=False,default="open"); subtotal=Column(Numeric(18,2),nullable=False,default=0); discount=Column(Numeric(18,2),nullable=False,default=0); tax=Column(Numeric(18,2),nullable=False,default=0); grand_total=Column(Numeric(18,2),nullable=False,default=0); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("tenant_id","order_number",name="uq_pos_orders_tenant_number"),)
class POSOrderLine(Base):
    __tablename__="pos_order_lines"
    id=Column(Integer,primary_key=True); order_id=Column(Integer,ForeignKey("pos_orders.id",ondelete="CASCADE"),nullable=False); product_id=Column(Integer,ForeignKey("products.id",ondelete="RESTRICT"),nullable=False); quantity=Column(Numeric(18,6),nullable=False); unit_price=Column(Numeric(18,2),nullable=False); line_total=Column(Numeric(18,2),nullable=False)
