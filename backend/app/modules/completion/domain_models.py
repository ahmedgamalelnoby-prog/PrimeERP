from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class FinanceAgingSnapshot(Base):
    __tablename__="finance_aging_snapshots"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    partner_id=Column(Integer,ForeignKey("commerce_partners.id",ondelete="RESTRICT"),nullable=False,index=True)
    direction=Column(String(10),nullable=False)
    as_of_date=Column(Date,nullable=False)
    current_amount=Column(Numeric(20,6),nullable=False,server_default="0")
    bucket_1_30=Column(Numeric(20,6),nullable=False,server_default="0")
    bucket_31_60=Column(Numeric(20,6),nullable=False,server_default="0")
    bucket_61_90=Column(Numeric(20,6),nullable=False,server_default="0")
    bucket_91_plus=Column(Numeric(20,6),nullable=False,server_default="0")
    total_amount=Column(Numeric(20,6),nullable=False,server_default="0")
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("direction IN ('ar','ap')",name="ck_aging_direction"),UniqueConstraint("company_id","partner_id","direction","as_of_date",name="uq_aging_snapshot"))

class FinanceWriteOff(Base):
    __tablename__="finance_writeoffs"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    partner_id=Column(Integer,ForeignKey("commerce_partners.id",ondelete="RESTRICT"),nullable=False,index=True)
    document_kind=Column(String(10),nullable=False)
    document_id=Column(Integer,nullable=False,index=True)
    amount=Column(Numeric(20,6),nullable=False)
    reason=Column(Text,nullable=False)
    status=Column(String(20),nullable=False,server_default="requested")
    approved_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    posted_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("document_kind IN ('sale','purchase')",name="ck_writeoff_kind"),CheckConstraint("amount > 0",name="ck_writeoff_amount"),CheckConstraint("status IN ('requested','approved','rejected','posted','cancelled')",name="ck_writeoff_status"))

class FinanceReconciliation(Base):
    __tablename__="finance_reconciliations"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    reconciliation_type=Column(String(40),nullable=False)
    source_ref=Column(String(160),nullable=False)
    target_ref=Column(String(160))
    source_amount=Column(Numeric(20,6),nullable=False,server_default="0")
    target_amount=Column(Numeric(20,6),nullable=False,server_default="0")
    tolerance=Column(Numeric(20,6),nullable=False,server_default="0")
    difference=Column(Numeric(20,6),nullable=False,server_default="0")
    status=Column(String(20),nullable=False,server_default="unmatched")
    reconciled_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    reconciled_at=Column(DateTime(timezone=True))
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class InventoryTraceUnit(Base):
    __tablename__="inventory_trace_units"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False,index=True)
    variant_id=Column(Integer,ForeignKey("product_variants.id",ondelete="RESTRICT"),nullable=True,index=True)
    trace_type=Column(String(10),nullable=False)
    code=Column(String(120),nullable=False)
    barcode=Column(String(120))
    lot_number=Column(String(120))
    serial_number=Column(String(120))
    manufacture_date=Column(Date)
    expiry_date=Column(Date)
    quantity=Column(Numeric(20,6),nullable=False,server_default="0")
    status=Column(String(20),nullable=False,server_default="active")
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("trace_type IN ('lot','serial')",name="ck_trace_type"),CheckConstraint("quantity >= 0",name="ck_trace_qty"),UniqueConstraint("company_id","trace_type","code",name="uq_trace_code"))

class ManufacturingWorkOrder(Base):
    __tablename__="manufacturing_work_orders"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    warehouse_id=Column(Integer,ForeignKey("inventory_warehouses.id",ondelete="RESTRICT"),nullable=True)
    item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False,index=True)
    variant_id=Column(Integer,ForeignKey("product_variants.id",ondelete="RESTRICT"),nullable=True)
    recipe_id=Column(Integer,ForeignKey("recipes.id",ondelete="RESTRICT"),nullable=True)
    number=Column(String(80),nullable=False)
    planned_qty=Column(Numeric(20,6),nullable=False)
    completed_qty=Column(Numeric(20,6),nullable=False,server_default="0")
    status=Column(String(20),nullable=False,server_default="draft")
    planned_start=Column(Date)
    planned_end=Column(Date)
    actual_start=Column(Date)
    actual_end=Column(Date)
    total_material_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    total_labor_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    total_overhead_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("company_id","number",name="uq_work_order_number"),CheckConstraint("planned_qty > 0",name="ck_work_order_planned_qty"),CheckConstraint("completed_qty >= 0",name="ck_work_order_completed_qty"),CheckConstraint("status IN ('draft','released','in_progress','completed','cancelled','closed')",name="ck_work_order_status"))

class ManufacturingConsumption(Base):
    __tablename__="manufacturing_consumptions"
    id=Column(Integer,primary_key=True)
    work_order_id=Column(Integer,ForeignKey("manufacturing_work_orders.id",ondelete="CASCADE"),nullable=False,index=True)
    item_id=Column(Integer,ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False)
    quantity=Column(Numeric(20,6),nullable=False)
    unit_cost=Column(Numeric(20,6),nullable=False,server_default="0")
    stock_move_id=Column(Integer,ForeignKey("inventory_stock_moves.id",ondelete="RESTRICT"),nullable=True)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class CRMOpportunity(Base):
    __tablename__="crm_opportunities"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    partner_id=Column(Integer,ForeignKey("commerce_partners.id",ondelete="RESTRICT"),nullable=False,index=True)
    code=Column(String(80),nullable=False)
    stage=Column(String(40),nullable=False,server_default="new")
    value=Column(Numeric(20,6),nullable=False,server_default="0")
    probability=Column(Numeric(6,3),nullable=False,server_default="0")
    expected_close=Column(Date)
    owner_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    status=Column(String(20),nullable=False,server_default="open")
    lost_reason=Column(Text)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("company_id","code",name="uq_crm_opportunity_code"),CheckConstraint("probability >= 0 AND probability <= 100",name="ck_crm_probability"),CheckConstraint("status IN ('open','won','lost','cancelled')",name="ck_crm_opportunity_status"))

class CRMActivity(Base):
    __tablename__="crm_activities"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    opportunity_id=Column(Integer,ForeignKey("crm_opportunities.id",ondelete="CASCADE"),nullable=True,index=True)
    partner_id=Column(Integer,ForeignKey("commerce_partners.id",ondelete="RESTRICT"),nullable=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    activity_type=Column(String(30),nullable=False)
    subject=Column(String(200),nullable=False)
    due_at=Column(DateTime(timezone=True))
    completed_at=Column(DateTime(timezone=True))
    notes=Column(Text)

class HRAttendance(Base):
    __tablename__="hr_attendance_records"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    employee_user_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False,index=True)
    work_date=Column(Date,nullable=False)
    check_in=Column(DateTime(timezone=True))
    check_out=Column(DateTime(timezone=True))
    overtime_minutes=Column(Integer,nullable=False,server_default="0")
    status=Column(String(20),nullable=False,server_default="present")
    __table_args__=(UniqueConstraint("company_id","employee_user_id","work_date",name="uq_hr_attendance_day"),)

class HRLeave(Base):
    __tablename__="hr_leave_requests"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    employee_user_id=Column(Integer,ForeignKey("users.id",ondelete="RESTRICT"),nullable=False,index=True)
    leave_type=Column(String(40),nullable=False)
    start_date=Column(Date,nullable=False)
    end_date=Column(Date,nullable=False)
    status=Column(String(20),nullable=False,server_default="requested")
    reason=Column(Text)
    approved_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    __table_args__=(CheckConstraint("end_date >= start_date",name="ck_hr_leave_dates"),CheckConstraint("status IN ('requested','approved','rejected','cancelled')",name="ck_hr_leave_status"))

class HRPayrollCompletionRun(Base):
    __tablename__="hr_payroll_completion_runs"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    period_key=Column(String(20),nullable=False)
    status=Column(String(20),nullable=False,server_default="draft")
    total_gross=Column(Numeric(20,6),nullable=False,server_default="0")
    total_deductions=Column(Numeric(20,6),nullable=False,server_default="0")
    total_net=Column(Numeric(20,6),nullable=False,server_default="0")
    posted_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="SET NULL"))
    __table_args__=(UniqueConstraint("company_id","period_key",name="uq_hr_payroll_completion_period"),)

class TaxFilingControl(Base):
    __tablename__="tax_filing_controls"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    tax_type=Column(String(30),nullable=False)
    period_key=Column(String(20),nullable=False)
    status=Column(String(20),nullable=False,server_default="draft")
    output_tax=Column(Numeric(20,6),nullable=False,server_default="0")
    input_tax=Column(Numeric(20,6),nullable=False,server_default="0")
    withholding_tax=Column(Numeric(20,6),nullable=False,server_default="0")
    payable_tax=Column(Numeric(20,6),nullable=False,server_default="0")
    submission_ref=Column(String(160))
    submitted_at=Column(DateTime(timezone=True))
    __table_args__=(UniqueConstraint("company_id","tax_type","period_key",name="uq_tax_filing_period"),)

class SubscriptionLifecycleEvent(Base):
    __tablename__="subscription_lifecycle_events"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    subscription_id=Column(Integer,ForeignKey("subscriptions.id",ondelete="CASCADE"),nullable=False,index=True)
    event_type=Column(String(40),nullable=False)
    from_status=Column(String(30))
    to_status=Column(String(30),nullable=False)
    reason=Column(Text)
    actor_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class APIClientCredential(Base):
    __tablename__="api_client_credentials"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=True,index=True)
    name=Column(String(120),nullable=False)
    key_prefix=Column(String(30),nullable=False)
    secret_hash=Column(String(128),nullable=False)
    scopes=Column(Text,nullable=False,server_default="[]")
    is_active=Column(Boolean,nullable=False,server_default="true")
    expires_at=Column(DateTime(timezone=True))
    last_used_at=Column(DateTime(timezone=True))
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("tenant_id","key_prefix",name="uq_api_key_prefix"),)

class WebhookDeliveryControl(Base):
    __tablename__="webhook_delivery_controls"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=True,index=True)
    event_type=Column(String(100),nullable=False)
    endpoint=Column(String(500),nullable=False)
    payload=Column(Text,nullable=False,server_default="{}")
    status=Column(String(20),nullable=False,server_default="pending")
    attempts=Column(Integer,nullable=False,server_default="0")
    max_attempts=Column(Integer,nullable=False,server_default="8")
    next_attempt_at=Column(DateTime(timezone=True))
    last_error=Column(Text)
    delivered_at=Column(DateTime(timezone=True))

class MobileSyncQueue(Base):
    __tablename__="mobile_sync_queue"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    device_id=Column(String(120),nullable=False)
    idempotency_key=Column(String(180),nullable=False)
    entity_type=Column(String(60),nullable=False)
    entity_id=Column(String(120))
    operation=Column(String(20),nullable=False)
    payload=Column(Text,nullable=False,server_default="{}")
    status=Column(String(20),nullable=False,server_default="pending")
    error=Column(Text)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("tenant_id","device_id","idempotency_key",name="uq_mobile_sync_idempotency"),)

class WorkflowInstance(Base):
    __tablename__="workflow_instances"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    module=Column(String(60),nullable=False)
    document_type=Column(String(80),nullable=False)
    document_id=Column(String(120),nullable=False)
    status=Column(String(20),nullable=False,server_default="pending")
    current_level=Column(Integer,nullable=False,server_default="1")
    delegated_to=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    due_at=Column(DateTime(timezone=True))
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("tenant_id","module","document_type","document_id",name="uq_workflow_instance_document"),)

class WorkflowApprovalStep(Base):
    __tablename__="workflow_approval_steps"
    id=Column(Integer,primary_key=True)
    workflow_id=Column(Integer,ForeignKey("workflow_instances.id",ondelete="CASCADE"),nullable=False,index=True)
    level=Column(Integer,nullable=False)
    approver_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    status=Column(String(20),nullable=False,server_default="pending")
    reason=Column(Text)
    decided_at=Column(DateTime(timezone=True))
    __table_args__=(UniqueConstraint("workflow_id","level",name="uq_workflow_step_level"),)
