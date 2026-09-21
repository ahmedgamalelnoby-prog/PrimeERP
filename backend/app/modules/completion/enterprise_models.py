from sqlalchemy import Column,Integer,String,Text,Boolean,Numeric,DateTime,ForeignKey,UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database.base import Base
class DomainControl(Base):
 __tablename__="domain_controls"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);module=Column(String(60),nullable=False);document_type=Column(String(80),nullable=False);document_id=Column(String(120),nullable=False);state=Column(String(40),nullable=False,default="draft");approval_required=Column(Boolean,nullable=False,default=False);approved=Column(Boolean,nullable=False,default=False);posted=Column(Boolean,nullable=False,default=False);reversed=Column(Boolean,nullable=False,default=False);payload=Column(JSONB,nullable=False,server_default="{}");created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False);updated_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 __table_args__=(UniqueConstraint("tenant_id","module","document_type","document_id",name="uq_domain_control_document"),)
class WorkflowRule(Base):
 __tablename__="universal_workflow_rules"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);module=Column(String(60),nullable=False);document_type=Column(String(80),nullable=False);condition_json=Column(JSONB,nullable=False,server_default="{}");approval_levels=Column(Integer,nullable=False,default=1);delegation_allowed=Column(Boolean,nullable=False,default=False);escalation_minutes=Column(Integer,nullable=True);is_active=Column(Boolean,nullable=False,default=True)
class MasterDataIdentity(Base):
 __tablename__="master_data_identities"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);entity_type=Column(String(40),nullable=False);entity_id=Column(String(120),nullable=False);canonical_key=Column(String(180),nullable=False);external_ids=Column(JSONB,nullable=False,server_default="{}");active=Column(Boolean,nullable=False,default=True);__table_args__=(UniqueConstraint("tenant_id","entity_type","canonical_key",name="uq_master_identity"),)
class AIActionAudit(Base):
 __tablename__="ai_action_audits"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);user_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"));action=Column(String(100),nullable=False);input_json=Column(JSONB,nullable=False,server_default="{}");recommendation=Column(Text);approved=Column(Boolean,nullable=False,default=False);executed=Column(Boolean,nullable=False,default=False);created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
class SubscriptionUsage(Base):
 __tablename__="subscription_usage"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);metric=Column(String(80),nullable=False);period_key=Column(String(30),nullable=False);used=Column(Numeric(20,4),nullable=False,server_default="0");limit_value=Column(Numeric(20,4));updated_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False);__table_args__=(UniqueConstraint("tenant_id","metric","period_key",name="uq_subscription_usage"),)
