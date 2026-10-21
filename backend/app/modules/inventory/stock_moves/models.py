from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class InventoryAccountingConfig(Base):
    __tablename__ = "inventory_accounting_configs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    journal_id = Column(Integer, ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False)
    inventory_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    cogs_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    adjustment_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    clearing_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    is_active = Column(String(1), nullable=False, default="Y")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "company_id", name="uq_inventory_accounting_config_scope"),
        CheckConstraint("is_active IN ('Y','N')", name="ck_inventory_accounting_config_active"),
    )


class InventoryStockMove(Base):
    __tablename__ = "inventory_stock_moves"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    source_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=True, index=True)
    destination_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    movement_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    reference = Column(String(100), nullable=True, index=True)
    source_module = Column(String(80), nullable=True)
    source_entity = Column(String(80), nullable=True)
    source_id = Column(String(80), nullable=True)
    notes = Column(Text, nullable=True)
    transaction_date = Column(Date, nullable=False, server_default=func.current_date(), index=True)
    posted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    accounting_entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="RESTRICT"), nullable=True, index=True)
    reversed_by_move_id = Column(Integer, ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), nullable=True, index=True)
    reservation_id = Column(Integer, ForeignKey("inventory_reservations.id", ondelete="RESTRICT"), nullable=True, index=True)

    item = relationship("InventoryItem")
    variant = relationship("ProductVariant")
    source_location = relationship("InventoryLocation", foreign_keys=[source_location_id])
    destination_location = relationship("InventoryLocation", foreign_keys=[destination_location_id])
    accounting_entry = relationship("JournalEntry", foreign_keys=[accounting_entry_id])
    reversed_by_move = relationship("InventoryStockMove", remote_side=[id], foreign_keys=[reversed_by_move_id], uselist=False)
    reservation = relationship("InventoryReservation", foreign_keys=[reservation_id])
    valuation_allocations = relationship("InventoryValuationAllocation", back_populates="stock_move", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_stock_move_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_inventory_stock_move_unit_cost"),
        CheckConstraint("movement_type IN ('receipt','issue','transfer','adjustment','opening','return','production_issue','production_receipt')", name="ck_inventory_stock_move_type"),
        CheckConstraint("status IN ('draft','posted','cancelled','reversed')", name="ck_inventory_stock_move_status"),
        CheckConstraint("source_location_id IS NOT NULL OR destination_location_id IS NOT NULL", name="ck_inventory_stock_move_endpoint"),
        CheckConstraint("source_location_id IS NULL OR destination_location_id IS NULL OR source_location_id <> destination_location_id", name="ck_inventory_stock_move_distinct_endpoints"),
        CheckConstraint("status <> 'posted' OR movement_type = 'transfer' OR accounting_entry_id IS NOT NULL", name="ck_inventory_stock_move_posted_accounting"),
        Index("uq_inventory_stock_move_source_nonnull", "company_id", "source_module", "source_entity", "source_id", unique=True, postgresql_where=(source_module.is_not(None) & source_entity.is_not(None) & source_id.is_not(None))),
    )


class InventoryCostLayer(Base):
    __tablename__ = "inventory_cost_layers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    receipt_move_id = Column(Integer, ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_remaining = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)

    receipt_move = relationship("InventoryStockMove")
    variant = relationship("ProductVariant")

    __table_args__ = (
        CheckConstraint("quantity_remaining >= 0", name="ck_inventory_cost_layer_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_inventory_cost_layer_unit_cost"),
    )


class InventoryValuationAllocation(Base):
    __tablename__ = "inventory_valuation_allocations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_move_id = Column(Integer, ForeignKey("inventory_stock_moves.id", ondelete="CASCADE"), nullable=False, index=True)
    cost_layer_id = Column(Integer, ForeignKey("inventory_cost_layers.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    allocation_role = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    stock_move = relationship("InventoryStockMove", back_populates="valuation_allocations")
    cost_layer = relationship("InventoryCostLayer")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_valuation_allocation_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_inventory_valuation_allocation_unit_cost"),
        CheckConstraint("allocation_role IN ('source_consumed','destination_added')", name="ck_inventory_valuation_allocation_role"),
    )
