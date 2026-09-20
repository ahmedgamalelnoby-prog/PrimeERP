from sqlalchemy import Column,Integer,Numeric,String,DateTime,ForeignKey,Date,Text,Boolean,CheckConstraint,UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class ManufacturingLaborActual(Base):
    __tablename__="manufacturing_labor_actuals"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    work_order_id=Column(Integer,ForeignKey("manufacturing_work_orders.id",ondelete="CASCADE"),nullable=False,index=True)
    user_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=True)
    work_date=Column(Date,nullable=False)
    minutes=Column(Numeric(12,2),nullable=False)
    hourly_rate=Column(Numeric(18,6),nullable=False)
    amount=Column(Numeric(20,6),nullable=False)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("minutes > 0","ck_mfg_labor_minutes"),CheckConstraint("hourly_rate >= 0 AND amount >= 0","ck_mfg_labor_amount"),)

class ManufacturingOverheadActual(Base):
    __tablename__="manufacturing_overhead_actuals"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    work_order_id=Column(Integer,ForeignKey("manufacturing_work_orders.id",ondelete="CASCADE"),nullable=False,index=True)
    cost_code=Column(String(80),nullable=False)
    amount=Column(Numeric(20,6),nullable=False)
    description=Column(Text)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("amount >= 0","ck_mfg_overhead_amount"),)

class ManufacturingScrap(Base):
    __tablename__="manufacturing_scrap"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    work_order_id=Column(Integer,ForeignKey("manufacturing_work_orders.id",ondelete="CASCADE"),nullable=False,index=True)
    item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False)
    variant_id=Column(Integer,ForeignKey("product_variants.id",ondelete="RESTRICT"))
    quantity=Column(Numeric(20,6),nullable=False)
    unit_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    reason=Column(String(300),nullable=False)
    stock_move_id=Column(Integer,ForeignKey("inventory_stock_moves.id",ondelete="SET NULL"))
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("quantity > 0 AND unit_cost >= 0","ck_mfg_scrap_values"),)

class ManufacturingByProduct(Base):
    __tablename__="manufacturing_byproducts"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    work_order_id=Column(Integer,ForeignKey("manufacturing_work_orders.id",ondelete="CASCADE"),nullable=False,index=True)
    item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False)
    variant_id=Column(Integer,ForeignKey("product_variants.id",ondelete="RESTRICT"))
    quantity=Column(Numeric(20,6),nullable=False)
    unit_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    stock_move_id=Column(Integer,ForeignKey("inventory_stock_moves.id",ondelete="SET NULL"))
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("quantity > 0 AND unit_cost >= 0","ck_mfg_byproduct_values"),)

class ManufacturingSubcontract(Base):
    __tablename__="manufacturing_subcontracts"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    work_order_id=Column(Integer,ForeignKey("manufacturing_work_orders.id",ondelete="CASCADE"),nullable=False,index=True)
    vendor_id=Column(Integer,ForeignKey("commerce_partners.id",ondelete="RESTRICT"),nullable=False)
    service_reference=Column(String(120),nullable=False)
    planned_quantity=Column(Numeric(20,6),nullable=False)
    actual_quantity=Column(Numeric(20,6),nullable=False,server_default="0")
    unit_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    status=Column(String(20),nullable=False,server_default="planned")
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("planned_quantity > 0 AND actual_quantity >= 0 AND unit_cost >= 0","ck_mfg_subcontract_values"),CheckConstraint("status IN ('planned','sent','received','cancelled')","ck_mfg_subcontract_status"),)

class ManufacturingVariance(Base):
    __tablename__="manufacturing_variances"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    work_order_id=Column(Integer,ForeignKey("manufacturing_work_orders.id",ondelete="CASCADE"),nullable=False,index=True)
    planned_material=Column(Numeric(20,6),nullable=False,server_default="0")
    actual_material=Column(Numeric(20,6),nullable=False,server_default="0")
    planned_labor=Column(Numeric(20,6),nullable=False,server_default="0")
    planned_quantity=Column(Numeric(20,6),nullable=False,server_default="0")
    actual_quantity=Column(Numeric(20,6),nullable=False,server_default="0")
    actual_labor=Column(Numeric(20,6),nullable=False,server_default="0")
    planned_overhead=Column(Numeric(20,6),nullable=False,server_default="0")
    actual_overhead=Column(Numeric(20,6),nullable=False,server_default="0")
    scrap_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    byproduct_credit=Column(Numeric(20,6),nullable=False,server_default="0")
    subcontract_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    total_variance=Column(Numeric(20,6),nullable=False,server_default="0")
    journal_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="SET NULL"))
    wip_journal_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="SET NULL"))
    status=Column(String(20),nullable=False,server_default="calculated")
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("work_order_id","status",name="uq_mfg_variance_work_order_status"),CheckConstraint("status IN ('calculated','posted','reversed')","ck_mfg_variance_status"),)

class InventoryStockPolicy(Base):
    __tablename__="inventory_stock_policies"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False)
    warehouse_id=Column(Integer,ForeignKey("inventory_warehouses.id",ondelete="CASCADE"),nullable=True)
    allow_negative=Column(Boolean,nullable=False,server_default="false")
    warning_threshold=Column(Numeric(20,6),nullable=False,server_default="0")
    costing_method=Column(String(20),nullable=False,server_default="weighted_average")
    is_active=Column(Boolean,nullable=False,server_default="true")
    __table_args__=(UniqueConstraint("company_id","warehouse_id","is_active",name="uq_inventory_policy_scope"),CheckConstraint("costing_method IN ('standard','weighted_average','fifo','actual')","ck_inventory_policy_costing"),)

class InventoryCostReconciliation(Base):
    __tablename__="inventory_cost_reconciliations"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False,index=True)
    warehouse_id=Column(Integer,ForeignKey("inventory_warehouses.id",ondelete="RESTRICT"),nullable=False,index=True)
    method=Column(String(20),nullable=False)
    quantity=Column(Numeric(20,6),nullable=False)
    subledger_value=Column(Numeric(20,6),nullable=False)
    recomputed_value=Column(Numeric(20,6),nullable=False)
    difference=Column(Numeric(20,6),nullable=False)
    status=Column(String(20),nullable=False,server_default="matched")
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("method IN ('standard','weighted_average','fifo','actual')","ck_cost_recon_method"),CheckConstraint("status IN ('matched','variance')","ck_cost_recon_status"),)
