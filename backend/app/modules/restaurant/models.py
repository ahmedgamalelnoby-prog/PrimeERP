from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Index,
    CheckConstraint,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

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

class PosOutlet(Base):
    """A food & beverage service location, e.g. Sea Restaurant or Pool Bar."""

    __tablename__ = "pos_outlets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=True, index=True)
    code = Column(String(40), nullable=False)
    name = Column(String(160), nullable=False)
    outlet_type = Column(String(30), nullable=False, default="restaurant")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_pos_outlet_company_code"),)


class PosOutletStation(Base):
    """Allowed production stations for an outlet."""

    __tablename__ = "pos_outlet_stations"

    id = Column(Integer, primary_key=True)
    outlet_id = Column(Integer, ForeignKey("pos_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("preparation_stations.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("outlet_id", "station_id", name="uq_pos_outlet_station"),)


class PosTerminal(Base):
    """A physical POS machine/cashier terminal assigned to one outlet."""

    __tablename__ = "pos_terminals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    outlet_id = Column(Integer, ForeignKey("pos_outlets.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(60), nullable=False)
    name = Column(String(160), nullable=False)
    device_identifier = Column(String(160), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_pos_terminal_company_code"),
        UniqueConstraint("company_id", "device_identifier", name="uq_pos_terminal_company_device"),
    )


class PosTerminalMenu(Base):
    """Menus enabled on a terminal; price list is authoritative for menu pricing."""

    __tablename__ = "pos_terminal_menus"

    id = Column(Integer, primary_key=True)
    terminal_id = Column(Integer, ForeignKey("pos_terminals.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True)
    price_list_id = Column(Integer, ForeignKey("product_price_lists.id", ondelete="RESTRICT"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("terminal_id", "menu_id", name="uq_pos_terminal_menu"),)


class PosMenuItemRoute(Base):
    """Routes a menu item from a terminal to the station that produces it."""

    __tablename__ = "pos_menu_item_routes"

    id = Column(Integer, primary_key=True)
    terminal_id = Column(Integer, ForeignKey("pos_terminals.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("preparation_stations.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("terminal_id", "menu_item_id", name="uq_pos_terminal_menu_item_route"),)


class PosOrderLineRoute(Base):
    """Production routing/status for a POS sales line."""

    __tablename__ = "pos_order_line_routes"

    id = Column(Integer, primary_key=True)
    sales_line_id = Column(Integer, ForeignKey("sales_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    terminal_id = Column(Integer, ForeignKey("pos_terminals.id", ondelete="RESTRICT"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("preparation_stations.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="queued")
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint("sales_line_id", name="uq_pos_order_line_route"),)


class PosCashierShift(Base):
    """Cashier shift with company-scoped cash reconciliation."""

    __tablename__ = "pos_cashier_shifts"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    terminal_id = Column(Integer, ForeignKey("pos_terminals.id", ondelete="RESTRICT"), nullable=False, index=True)
    opened_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    closed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    opening_cash = Column(Numeric(18, 4), nullable=False, default=0)
    expected_cash = Column(Numeric(18, 4), nullable=True)
    counted_cash = Column(Numeric(18, 4), nullable=True)
    variance = Column(Numeric(18, 4), nullable=True)
    status = Column(String(20), nullable=False, default="open")
    opened_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    closed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("opening_cash >= 0", name="ck_pos_cashier_shift_opening_cash"),
        CheckConstraint("status IN ('open','closed')", name="ck_pos_cashier_shift_status"),
        CheckConstraint(
            "(status = 'open' AND closed_at IS NULL AND expected_cash IS NULL AND counted_cash IS NULL AND variance IS NULL) OR "
            "(status = 'closed' AND closed_at IS NOT NULL AND expected_cash IS NOT NULL AND counted_cash IS NOT NULL AND variance IS NOT NULL)",
            name="ck_pos_cashier_shift_close_values",
        ),
        Index(
            "uq_pos_cashier_shift_open_terminal",
            "terminal_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
            sqlite_where=text("status = 'open'"),
        ),
    )
