from sqlalchemy import Column,Integer,ForeignKey,String,Boolean,Numeric,DateTime,Date,Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base
class ShippingCarrier(Base):
 __tablename__="shipping_carriers"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);code=Column(String(50),nullable=False);name=Column(String(150),nullable=False);is_active=Column(Boolean,nullable=False,default=True)
class ShippingCarrierRule(Base):
 __tablename__="shipping_carrier_rules"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False);carrier_id=Column(Integer,ForeignKey("shipping_carriers.id",ondelete="CASCADE"),nullable=False);rule_type=Column(String(30),nullable=False);fixed_amount=Column(Numeric(18,2),default=0);rate_percent=Column(Numeric(9,4),default=0);amount_per_kg=Column(Numeric(18,4),default=0);amount_per_item=Column(Numeric(18,4),default=0);zone=Column(String(80));cod_fee=Column(Numeric(18,2),default=0);visa_withdrawal_fee=Column(Numeric(18,2),default=0);priority=Column(Integer,default=100);is_active=Column(Boolean,default=True)
class Shipment(Base):
 __tablename__="shipments"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="RESTRICT"),nullable=False);branch_id=Column(Integer,ForeignKey("branches.id",ondelete="RESTRICT"),nullable=False);sales_order_id=Column(Integer,ForeignKey("sales_orders.id",ondelete="SET NULL"));carrier_id=Column(Integer,ForeignKey("shipping_carriers.id",ondelete="RESTRICT"));shipment_number=Column(String(80),nullable=False);tracking_number=Column(String(150));status=Column(String(30),nullable=False,default="preparing",index=True);payment_method=Column(String(30));cod_amount=Column(Numeric(18,2),default=0);shipping_charge=Column(Numeric(18,2),default=0);carrier_charge=Column(Numeric(18,2),default=0);customer_amount=Column(Numeric(18,2),default=0);dispatched_at=Column(DateTime(timezone=True));delivered_at=Column(DateTime(timezone=True));returned_at=Column(DateTime(timezone=True));notes=Column(Text);created_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"));created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 lines=relationship("ShipmentItem",cascade="all, delete-orphan")
class ShipmentItem(Base):
 __tablename__="shipment_items"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False);shipment_id=Column(Integer,ForeignKey("shipments.id",ondelete="CASCADE"),nullable=False);product_id=Column(Integer,ForeignKey("products.id",ondelete="RESTRICT"),nullable=False);quantity=Column(Numeric(18,6),nullable=False)
class ShippingReturn(Base):
 __tablename__="shipping_returns"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False);shipment_id=Column(Integer,ForeignKey("shipments.id",ondelete="RESTRICT"),nullable=False);reason=Column(Text);status=Column(String(30),default="requested");created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
class CarrierSettlement(Base):
 __tablename__="carrier_settlements"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False);carrier_id=Column(Integer,ForeignKey("shipping_carriers.id",ondelete="RESTRICT"),nullable=False);settlement_number=Column(String(80),nullable=False);settlement_date=Column(Date,nullable=False);orders_amount=Column(Numeric(18,2),default=0);carrier_charges=Column(Numeric(18,2),default=0);cod_collected=Column(Numeric(18,2),default=0);net_amount=Column(Numeric(18,2),default=0);status=Column(String(20),default="draft")