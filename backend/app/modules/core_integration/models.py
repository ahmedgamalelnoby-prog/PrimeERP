from datetime import datetime
from sqlalchemy import Column,Integer,String,DateTime,Text,Boolean,UniqueConstraint,ForeignKey
from app.database.base import Base
class IntegrationTransaction(Base):
 __tablename__="integration_transactions"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);source_module=Column(String(80),nullable=False);source_entity=Column(String(120),nullable=False);source_id=Column(String(120),nullable=False);operation=Column(String(80),nullable=False);idempotency_key=Column(String(180),nullable=False);status=Column(String(30),nullable=False,default="completed");reversal_of_id=Column(Integer,ForeignKey("integration_transactions.id",ondelete="RESTRICT"));reason=Column(Text);actor_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"));created_at=Column(DateTime(timezone=True),nullable=False,default=datetime.utcnow);reversed=Column(Boolean,nullable=False,default=False)
 __table_args__=(UniqueConstraint("company_id","idempotency_key",name="uq_integration_tx_idempotency"),)
