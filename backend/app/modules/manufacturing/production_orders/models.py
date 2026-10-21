from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ManufacturingWorkOrder(Base):
    __tablename__ = "manufacturing_work_orders"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(String(60), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False, index=True)
    recipe_version = Column(Integer, nullable=False)
    output_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    output_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    source_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    destination_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    planned_quantity = Column(Numeric(18, 4), nullable=False)
    produced_quantity = Column(Numeric(18, 4), nullable=True)
    status = Column(String(20), nullable=False, default="planned", index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    released_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    completed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    lines = relationship("ManufacturingWorkOrderLine", back_populates="work_order", cascade="all, delete-orphan", order_by="ManufacturingWorkOrderLine.id")

    __table_args__ = (
        UniqueConstraint("company_id", "number", name="uq_manufacturing_work_order_company_number"),
        CheckConstraint("recipe_version > 0", name="ck_manufacturing_work_order_recipe_version"),
        CheckConstraint("planned_quantity > 0", name="ck_manufacturing_work_order_planned_qty"),
        CheckConstraint("produced_quantity IS NULL OR produced_quantity > 0", name="ck_manufacturing_work_order_produced_qty"),
        CheckConstraint("source_location_id <> destination_location_id", name="ck_manufacturing_work_order_locations"),
        CheckConstraint("status IN ('planned','released','completed','cancelled')", name="ck_manufacturing_work_order_status"),
        CheckConstraint(
            "(status IN ('planned','released','cancelled') AND produced_quantity IS NULL AND completed_at IS NULL) OR "
            "(status = 'completed' AND produced_quantity IS NOT NULL AND completed_at IS NOT NULL)",
            name="ck_manufacturing_work_order_completion",
        ),
        Index("ix_manufacturing_work_order_company_status", "company_id", "status"),
    )


class ManufacturingWorkOrderLine(Base):
    __tablename__ = "manufacturing_work_order_lines"

    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey("manufacturing_work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    source_recipe_line_id = Column(Integer, ForeignKey("recipe_lines.id", ondelete="RESTRICT"), nullable=False)
    ingredient_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_per_output = Column(Numeric(18, 8), nullable=False)
    issued_quantity = Column(Numeric(18, 4), nullable=True)
    issue_move_id = Column(Integer, ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), nullable=True, unique=True)

    work_order = relationship("ManufacturingWorkOrder", back_populates="lines")

    __table_args__ = (
        UniqueConstraint("work_order_id", "source_recipe_line_id", name="uq_manufacturing_work_order_recipe_line"),
        CheckConstraint("quantity_per_output > 0", name="ck_manufacturing_work_order_line_rate"),
        CheckConstraint("issued_quantity IS NULL OR issued_quantity > 0", name="ck_manufacturing_work_order_line_issued_qty"),
    )
