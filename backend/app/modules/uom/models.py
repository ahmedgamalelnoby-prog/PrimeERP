from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from app.database.base import Base

class UnitOfMeasure(Base):
    __tablename__ = 'units_of_measure'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    code = Column(String(30), nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    factor_to_base = Column(Numeric(18, 8), nullable=False, server_default='1')
    is_base = Column(Boolean, nullable=False, server_default='false')
    is_active = Column(Boolean, nullable=False, server_default='true')
    __table_args__ = (UniqueConstraint('company_id','code',name='uq_uom_company_code'), CheckConstraint('factor_to_base > 0',name='ck_uom_factor_positive'))
