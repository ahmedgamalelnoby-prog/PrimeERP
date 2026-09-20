from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Boolean, func, UniqueConstraint
from app.database.base import Base
class CRMLead(Base):
    __tablename__="crm_leads"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    name=Column(String(200),nullable=False); phone=Column(String(80)); email=Column(String(200)); source=Column(String(80)); status=Column(String(30),nullable=False,default="new"); owner_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL")); notes=Column(Text); created_at=Column(DateTime(timezone=True),server_default=func.now())
class CRMOpportunity(Base):
    __tablename__="crm_opportunities"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    lead_id=Column(Integer,ForeignKey("crm_leads.id",ondelete="SET NULL")); name=Column(String(200),nullable=False); stage=Column(String(40),nullable=False,default="qualification"); amount=Column(Numeric(18,4),nullable=False,default=0); probability=Column(Numeric(5,2),nullable=False,default=0); expected_close=Column(Date); owner_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL")); lost_reason=Column(String(255)); notes=Column(Text); created_at=Column(DateTime(timezone=True),server_default=func.now())
class CRMActivity(Base):
    __tablename__="crm_activities"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    lead_id=Column(Integer,ForeignKey("crm_leads.id",ondelete="CASCADE")); opportunity_id=Column(Integer,ForeignKey("crm_opportunities.id",ondelete="CASCADE")); activity_type=Column(String(40),nullable=False); subject=Column(String(255),nullable=False); due_at=Column(DateTime(timezone=True)); status=Column(String(30),nullable=False,default="open"); assigned_to=Column(Integer,ForeignKey("users.id",ondelete="SET NULL")); notes=Column(Text); completed_at=Column(DateTime(timezone=True))
