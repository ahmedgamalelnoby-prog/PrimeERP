from sqlalchemy import Column,Integer,Numeric,String,Boolean,DateTime,ForeignKey,CheckConstraint,UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class POSModifierGroup(Base):
    __tablename__="pos_modifier_groups"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    name=Column(String(120),nullable=False)
    min_select=Column(Integer,nullable=False,server_default="0")
    max_select=Column(Integer,nullable=False,server_default="1")
    is_active=Column(Boolean,nullable=False,server_default="true")
    __table_args__=(CheckConstraint("min_select >= 0 AND max_select >= min_select","ck_pos_modifier_limits"),)

class POSModifierOption(Base):
    __tablename__="pos_modifier_options"
    id=Column(Integer,primary_key=True)
    group_id=Column(Integer,ForeignKey("pos_modifier_groups.id",ondelete="CASCADE"),nullable=False,index=True)
    code=Column(String(60),nullable=False)
    name=Column(String(160),nullable=False)
    price_delta=Column(Numeric(18,4),nullable=False,server_default="0")
    is_active=Column(Boolean,nullable=False,server_default="true")
    __table_args__=(UniqueConstraint("group_id","code",name="uq_pos_modifier_option"),)

class POSPromotion(Base):
    __tablename__="pos_promotions"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    code=Column(String(80),nullable=False)
    name=Column(String(160),nullable=False)
    discount_percent=Column(Numeric(8,4),nullable=False,server_default="0")
    min_subtotal=Column(Numeric(18,4),nullable=False,server_default="0")
    max_discount=Column(Numeric(18,4))
    is_active=Column(Boolean,nullable=False,server_default="true")
    valid_from=Column(DateTime(timezone=True))
    valid_to=Column(DateTime(timezone=True))
    __table_args__=(UniqueConstraint("company_id","code",name="uq_pos_promotion_code"),CheckConstraint("discount_percent >= 0 AND discount_percent <= 100","ck_pos_promotion_pct"),CheckConstraint("min_subtotal >= 0","ck_pos_promotion_min"),)

class POSPromotionUse(Base):
    __tablename__="pos_promotion_uses"
    id=Column(Integer,primary_key=True)
    promotion_id=Column(Integer,ForeignKey("pos_promotions.id",ondelete="RESTRICT"),nullable=False,index=True)
    sales_document_id=Column(Integer,ForeignKey("sales_documents.id",ondelete="RESTRICT"),nullable=False,index=True)
    discount_amount=Column(Numeric(18,4),nullable=False)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("promotion_id","sales_document_id",name="uq_pos_promotion_use"),)
