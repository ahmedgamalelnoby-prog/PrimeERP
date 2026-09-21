from sqlalchemy import Column,Integer,Date,DateTime,Numeric,String,ForeignKey,Text,CheckConstraint
from sqlalchemy.sql import func
from app.database.base import Base
class InventoryCostRevaluation(Base):
    __tablename__="inventory_cost_revaluations"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False,index=True)
    warehouse_id=Column(Integer,ForeignKey("inventory_warehouses.id",ondelete="RESTRICT"),nullable=False,index=True)
    effective_date=Column(Date,nullable=False); old_unit_cost=Column(Numeric(18,4),nullable=False); new_unit_cost=Column(Numeric(18,4),nullable=False)
    quantity=Column(Numeric(18,4),nullable=False); delta_value=Column(Numeric(18,4),nullable=False); reason=Column(Text,nullable=False)
    status=Column(String(20),nullable=False,default="draft"); journal_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="RESTRICT"))
    created_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL")); posted_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now()); posted_at=Column(DateTime(timezone=True))
    __table_args__=(CheckConstraint("new_unit_cost >= 0",name="ck_inventory_reval_new_cost"),CheckConstraint("quantity >= 0",name="ck_inventory_reval_quantity"),CheckConstraint("status IN ('draft','posted','cancelled')",name="ck_inventory_reval_status"))
