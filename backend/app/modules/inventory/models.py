from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, TIMESTAMP, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class Warehouse(Base):
    __tablename__="warehouses"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    branch_id=Column(Integer,ForeignKey("branches.id",ondelete="CASCADE"),nullable=False,index=True)
    code=Column(String(50),nullable=False)
    name=Column(String(150),nullable=False)
    is_active=Column(Boolean,nullable=False,default=True,server_default="true",index=True)
    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now(),nullable=False)
    updated_at=Column(TIMESTAMP(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("tenant_id","code",name="uq_warehouses_tenant_code"),)

class WarehouseLocation(Base):
    __tablename__="warehouse_locations"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    warehouse_id=Column(Integer,ForeignKey("warehouses.id",ondelete="CASCADE"),nullable=False,index=True)
    parent_id=Column(Integer,ForeignKey("warehouse_locations.id",ondelete="CASCADE"),nullable=True,index=True)
    code=Column(String(50),nullable=False)
    name=Column(String(150),nullable=False)
    is_active=Column(Boolean,nullable=False,default=True,server_default="true",index=True)
    __table_args__=(UniqueConstraint("warehouse_id","code",name="uq_warehouse_locations_warehouse_code"),)

class StockBalance(Base):
    __tablename__="stock_balances"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    warehouse_id=Column(Integer,ForeignKey("warehouses.id",ondelete="CASCADE"),nullable=False,index=True)
    location_id=Column(Integer,ForeignKey("warehouse_locations.id",ondelete="CASCADE"),nullable=False,index=True)
    product_id=Column(Integer,ForeignKey("products.id",ondelete="RESTRICT"),nullable=False,index=True)
    quantity=Column(Numeric(18,6),nullable=False,server_default="0")
    reserved_quantity=Column(Numeric(18,6),nullable=False,server_default="0")
    __table_args__=(UniqueConstraint("tenant_id","location_id","product_id",name="uq_stock_balances_location_product"),CheckConstraint("quantity >= 0","ck_stock_balances_quantity_nonnegative"),CheckConstraint("reserved_quantity >= 0 AND reserved_quantity <= quantity","ck_stock_balances_reserved_valid"))

class StockMovement(Base):
    __tablename__="stock_movements"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    product_id=Column(Integer,ForeignKey("products.id",ondelete="RESTRICT"),nullable=False,index=True)
    warehouse_id=Column(Integer,ForeignKey("warehouses.id",ondelete="RESTRICT"),nullable=False,index=True)
    location_id=Column(Integer,ForeignKey("warehouse_locations.id",ondelete="RESTRICT"),nullable=False,index=True)
    movement_type=Column(String(30),nullable=False,index=True)
    quantity=Column(Numeric(18,6),nullable=False)
    reference_type=Column(String(50),nullable=True,index=True)
    reference_id=Column(Integer,nullable=True,index=True)
    notes=Column(Text,nullable=True)
    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("quantity > 0","ck_stock_movements_quantity_positive"),)

class StockTransfer(Base):
    __tablename__="stock_transfers"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    source_warehouse_id=Column(Integer,ForeignKey("warehouses.id",ondelete="RESTRICT"),nullable=False,index=True)
    destination_warehouse_id=Column(Integer,ForeignKey("warehouses.id",ondelete="RESTRICT"),nullable=False,index=True)
    status=Column(String(30),nullable=False,server_default="posted",index=True)
    notes=Column(Text,nullable=True)
    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now(),nullable=False)

class StockTransferLine(Base):
    __tablename__="stock_transfer_lines"
    id=Column(Integer,primary_key=True,index=True)
    transfer_id=Column(Integer,ForeignKey("stock_transfers.id",ondelete="CASCADE"),nullable=False,index=True)
    product_id=Column(Integer,ForeignKey("products.id",ondelete="RESTRICT"),nullable=False,index=True)
    source_location_id=Column(Integer,ForeignKey("warehouse_locations.id",ondelete="RESTRICT"),nullable=False,index=True)
    destination_location_id=Column(Integer,ForeignKey("warehouse_locations.id",ondelete="RESTRICT"),nullable=False,index=True)
    quantity=Column(Numeric(18,6),nullable=False)
    __table_args__=(CheckConstraint("quantity > 0","ck_stock_transfer_lines_quantity_positive"),)

class StockReservation(Base):
    __tablename__="stock_reservations"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    reference_type=Column(String(50),nullable=False,index=True)
    reference_id=Column(Integer,nullable=False,index=True)
    status=Column(String(30),nullable=False,server_default="reserved",index=True)
    notes=Column(Text,nullable=True)
    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now(),nullable=False)

class StockReservationLine(Base):
    __tablename__="stock_reservation_lines"
    id=Column(Integer,primary_key=True,index=True)
    reservation_id=Column(Integer,ForeignKey("stock_reservations.id",ondelete="CASCADE"),nullable=False,index=True)
    product_id=Column(Integer,ForeignKey("products.id",ondelete="RESTRICT"),nullable=False,index=True)
    location_id=Column(Integer,ForeignKey("warehouse_locations.id",ondelete="RESTRICT"),nullable=False,index=True)
    quantity=Column(Numeric(18,6),nullable=False)
    __table_args__=(CheckConstraint("quantity > 0","ck_stock_reservation_lines_quantity_positive"),)

class StockIssue(Base):
    __tablename__="stock_issues"
    id=Column(Integer,primary_key=True,index=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    warehouse_id=Column(Integer,ForeignKey("warehouses.id",ondelete="RESTRICT"),nullable=False,index=True)
    issue_type=Column(String(30),nullable=False,server_default="consumption",index=True)
    reference_type=Column(String(50),nullable=True,index=True)
    reference_id=Column(Integer,nullable=True,index=True)
    status=Column(String(30),nullable=False,server_default="posted",index=True)
    notes=Column(Text,nullable=True)
    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now(),nullable=False)

class StockIssueLine(Base):
    __tablename__="stock_issue_lines"
    id=Column(Integer,primary_key=True,index=True)
    issue_id=Column(Integer,ForeignKey("stock_issues.id",ondelete="CASCADE"),nullable=False,index=True)
    product_id=Column(Integer,ForeignKey("products.id",ondelete="RESTRICT"),nullable=False,index=True)
    location_id=Column(Integer,ForeignKey("warehouse_locations.id",ondelete="RESTRICT"),nullable=False,index=True)
    quantity=Column(Numeric(18,6),nullable=False)
    __table_args__=(CheckConstraint("quantity > 0","ck_stock_issue_lines_quantity_positive"),)
