from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text

from app.database.base import Base


class SallaSyncSettings(Base):
    __tablename__ = "salla_sync_settings"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=True)
    default_tax_rate_id = Column(Integer, ForeignKey("tax_rates.id", ondelete="RESTRICT"), nullable=True)
    customer_code_prefix = Column(String(20), nullable=False, default="SALLA-C-")
    product_code_prefix = Column(String(20), nullable=False, default="SALLA-P-")
    import_paid_orders = Column(Boolean, nullable=False, default=False)
    auto_fulfill_orders = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
