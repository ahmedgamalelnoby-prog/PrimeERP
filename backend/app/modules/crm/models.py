from sqlalchemy import Column,DateTime,ForeignKey,Integer,String,Text,func
from app.database.base import Base
class CRMLead(Base):
    __tablename__="crm_leads"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    name=Column(String(200),nullable=False); phone=Column(String(80)); email=Column(String(200)); source=Column(String(80)); status=Column(String(30),nullable=False,default="new"); owner_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL")); notes=Column(Text); created_at=Column(DateTime(timezone=True),server_default=func.now())
