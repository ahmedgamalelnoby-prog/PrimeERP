from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class POSOutlet(Base):
    __tablename__="pos_outlets"
    id=Column(Integer,primary_key=True,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    branch_id=Column(Integer,ForeignKey("branches.id",ondelete="RESTRICT"),nullable=False,index=True); inventory_location_id=Column(Integer,ForeignKey("inventory_locations.id",ondelete="RESTRICT"),nullable=False,index=True)
    code=Column(String(60),nullable=False); name=Column(String(200),nullable=False); is_active=Column(Boolean,nullable=False,default=True)
    __table_args__=(UniqueConstraint("company_id","code",name="uq_pos_outlet_company_code"),)
class POSDevice(Base):
    __tablename__="pos_devices"
    id=Column(Integer,primary_key=True,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); outlet_id=Column(Integer,ForeignKey("pos_outlets.id",ondelete="CASCADE"),nullable=False,index=True)
    code=Column(String(60),nullable=False); name=Column(String(160),nullable=False); is_active=Column(Boolean,nullable=False,default=True)
    __table_args__=(UniqueConstraint("company_id","code",name="uq_pos_device_company_code"),)
class POSSession(Base):
    __tablename__="pos_sessions"
    id=Column(Integer,primary_key=True,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); outlet_id=Column(Integer,ForeignKey("pos_outlets.id",ondelete="RESTRICT"),nullable=False,index=True); device_id=Column(Integer,ForeignKey("pos_devices.id",ondelete="RESTRICT"),nullable=False,index=True); cashier_user_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False,index=True)
    status=Column(String(20),nullable=False,default="open",index=True); opened_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now()); closed_at=Column(DateTime(timezone=True)); closing_total=Column(Numeric(18,4)); closing_cash=Column(Numeric(18,4)); closing_card=Column(Numeric(18,4)); closing_bank=Column(Numeric(18,4)); closing_other=Column(Numeric(18,4))
    __table_args__=(CheckConstraint("status IN ('open','closed','cancelled')",name="ck_pos_session_status"),)
class POSOrder(Base):
    __tablename__="pos_orders"
    id=Column(Integer,primary_key=True,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); session_id=Column(Integer,ForeignKey("pos_sessions.id",ondelete="RESTRICT"),nullable=False,index=True); number=Column(String(80),nullable=False); status=Column(String(20),nullable=False,default="draft",index=True)
    subtotal=Column(Numeric(18,4),nullable=False,default=0); tax_total=Column(Numeric(18,4),nullable=False,default=0); total=Column(Numeric(18,4),nullable=False,default=0); paid_total=Column(Numeric(18,4),nullable=False,default=0); finalized_at=Column(DateTime(timezone=True))
    __table_args__=(UniqueConstraint("company_id","number",name="uq_pos_order_company_number"),CheckConstraint("status IN ('draft','finalized','cancelled','reversed')",name="ck_pos_order_status"),)
class POSOrderLine(Base):
    __tablename__="pos_order_lines"
    id=Column(Integer,primary_key=True,index=True); order_id=Column(Integer,ForeignKey("pos_orders.id",ondelete="CASCADE"),nullable=False,index=True); item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False,index=True); variant_id=Column(Integer,ForeignKey("product_variants.id",ondelete="RESTRICT")); quantity=Column(Numeric(18,4),nullable=False); unit_price=Column(Numeric(18,4),nullable=False); tax_percent=Column(Numeric(8,4),nullable=False,default=0); line_subtotal=Column(Numeric(18,4),nullable=False); line_tax=Column(Numeric(18,4),nullable=False,default=0); line_total=Column(Numeric(18,4),nullable=False); recipe_id=Column(Integer,ForeignKey("recipes.id",ondelete="SET NULL"))
class POSPayment(Base):
    __tablename__="pos_payments"
    id=Column(Integer,primary_key=True,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); order_id=Column(Integer,ForeignKey("pos_orders.id",ondelete="RESTRICT"),nullable=False,index=True); method=Column(String(20),nullable=False); amount=Column(Numeric(18,4),nullable=False); idempotency_key=Column(String(120),nullable=False); status=Column(String(20),nullable=False,default="posted"); accounting_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="RESTRICT"),nullable=True,index=True); created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())
    __table_args__=(UniqueConstraint("company_id","idempotency_key",name="uq_pos_payment_idempotency"),CheckConstraint("method IN ('cash','card','bank','other')",name="ck_pos_payment_method"),CheckConstraint("amount > 0",name="ck_pos_payment_amount"),CheckConstraint("status IN ('posted','reversed')",name="ck_pos_payment_status"),)
