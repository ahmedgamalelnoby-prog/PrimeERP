from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Floor(Base):
    """
    صالات وأدوار المطعم.

    أمثلة:
    - الصالة الرئيسية
    - التراس
    - الدور الأول
    - منطقة كبار الزوار
    """

    __tablename__ = "restaurant_floors"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    branch_id = Column(
        Integer,
        ForeignKey(
            "branches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    code = Column(
        String(30),
        nullable=True,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    display_order = Column(
        Integer,
        default=0,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    tables = relationship(
        "RestaurantTable",
        back_populates="floor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Floor {self.name}>"


class RestaurantTable(Base):
    """
    طاولات المطعم.
    """

    __tablename__ = "restaurant_tables"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    branch_id = Column(
        Integer,
        ForeignKey(
            "branches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    floor_id = Column(
        Integer,
        ForeignKey(
            "restaurant_floors.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    code = Column(
        String(30),
        nullable=False,
        index=True,
    )

    capacity = Column(
        Integer,
        default=4,
        nullable=False,
    )

    shape = Column(
        String(30),
        default="square",
        nullable=False,
    )

    position_x = Column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )

    position_y = Column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )

    width = Column(
        Numeric(10, 2),
        default=100,
        nullable=False,
    )

    height = Column(
        Numeric(10, 2),
        default=100,
        nullable=False,
    )

    status = Column(
        String(30),
        default="available",
        nullable=False,
        index=True,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    floor = relationship(
        "Floor",
        back_populates="tables",
    )

    def __repr__(self) -> str:
        return f"<RestaurantTable {self.code}>"


class PreparationStation(Base):
    """
    محطات تحضير الطلبات داخل المطعم.

    أمثلة:
    - المطبخ الساخن
    - المطبخ البارد
    - المشروبات
    - الحلويات
    - الشواية
    """

    __tablename__ = "preparation_stations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    branch_id = Column(
        Integer,
        ForeignKey(
            "branches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    code = Column(
        String(30),
        nullable=False,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    station_type = Column(
        String(50),
        default="kitchen",
        nullable=False,
    )

    printer_name = Column(
        String(150),
        nullable=True,
    )

    display_order = Column(
        Integer,
        default=0,
        nullable=False,
    )

    is_kds_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_printer_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PreparationStation {self.name}>"


class OrderType(Base):
    """
    أنواع طلبات المطعم.

    أمثلة:
    - داخل المطعم Dine In
    - سفري Takeaway
    - توصيل Delivery
    - استلام من الفرع Pickup
    """

    __tablename__ = "restaurant_order_types"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    branch_id = Column(
        Integer,
        ForeignKey(
            "branches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    code = Column(
        String(30),
        nullable=False,
        index=True,
    )

    order_category = Column(
        String(30),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    service_charge_percentage = Column(
        Numeric(7, 4),
        default=0,
        nullable=False,
    )

    minimum_order_amount = Column(
        Numeric(14, 2),
        default=0,
        nullable=False,
    )

    requires_table = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    requires_customer = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    requires_delivery_address = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    display_order = Column(
        Integer,
        default=0,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<OrderType {self.name}>"