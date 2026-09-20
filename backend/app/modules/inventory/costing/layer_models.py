from sqlalchemy import Column,Integer,Numeric,String,DateTime,Date,ForeignKey,Index
from sqlalchemy.sql import func
from app.database.base import Base
class InventoryCostLayer(Base):
 __tablename__="inventory_cost_layers"
 id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False,index=True);warehouse_id=Column(Integer,ForeignKey("inventory_warehouses.id",ondelete="RESTRICT"),nullable=False,index=True);source_type=Column(String(40),nullable=False);source_id=Column(String(120),nullable=False);layer_date=Column(Date,nullable=False);unit_cost=Column(Numeric(20,8),nullable=False);quantity_in=Column(Numeric(20,8),nullable=False,default=0);quantity_out=Column(Numeric(20,8),nullable=False,default=0);currency_code=Column(String(3),nullable=False,default="EGP");created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
