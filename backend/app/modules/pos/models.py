from sqlalchemy import Boolean,Column,ForeignKey,Integer,String,UniqueConstraint
from app.database.base import Base
class POSOutlet(Base):
    __tablename__="pos_outlets"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="RESTRICT"),nullable=False); branch_id=Column(Integer,ForeignKey("branches.id",ondelete="RESTRICT"),nullable=False); warehouse_id=Column(Integer,ForeignKey("warehouses.id",ondelete="RESTRICT"),nullable=False); code=Column(String(50),nullable=False); name=Column(String(150),nullable=False); outlet_type=Column(String(30),nullable=False,default="restaurant"); is_active=Column(Boolean,nullable=False,default=True)
    __table_args__=(UniqueConstraint("tenant_id","code",name="uq_pos_outlets_tenant_code"),)
