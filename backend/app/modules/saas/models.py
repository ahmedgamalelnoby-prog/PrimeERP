from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
        index=True,
    )

    slug = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    business_type = Column(
        String(50),
        nullable=False,
        default="general",
        index=True,
    )

    owner_name = Column(
        String(150),
        nullable=False,
    )

    email = Column(
        String(255),
        nullable=False,
        index=True,
    )

    phone = Column(
        String(30),
        nullable=True,
    )

    country_code = Column(
        String(2),
        nullable=False,
        default="EG",
    )

    default_language = Column(
        String(5),
        nullable=False,
        default="ar",
    )

    default_locale = Column(
        String(10),
        nullable=False,
        default="ar-EG",
    )

    timezone = Column(
        String(50),
        nullable=False,
        default="Africa/Cairo",
    )

    currency_code = Column(
        String(3),
        nullable=False,
        default="EGP",
    )

    status = Column(
        String(30),
        nullable=False,
        default="trial",
        index=True,
    )

    is_trial = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    trial_started_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    trial_ends_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    suspended_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    suspension_reason = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Do not reference User.tenant_id here as a string expression.
    # User imports Tenant directly, so using "User.tenant_id" here can
    # fail when this module is imported on its own before the User mapper
    # has been registered. SQLAlchemy can infer the join from User.tenant_id.
    users = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    companies = relationship(
        "Company",
        back_populates="tenant",
        foreign_keys="Company.tenant_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    branches = relationship(
        "Branch",
        back_populates="tenant",
        foreign_keys="Branch.tenant_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    enabled_modules = relationship(
        "TenantModule",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Tenant "
            f"id={self.id} "
            f"slug={self.slug!r} "
            f"status={self.status!r}>"
        )


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name_ar = Column(String(150), nullable=False)
    name_en = Column(String(150), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    monthly_price = Column(Numeric(18, 2), nullable=False, default=0)
    yearly_price = Column(Numeric(18, 2), nullable=False, default=0)
    currency_code = Column(String(3), nullable=False, default="EGP")
    trial_days = Column(Integer, nullable=False, default=14)
    max_users = Column(Integer, nullable=False, default=5)
    max_companies = Column(Integer, nullable=False, default=1)
    max_branches = Column(Integer, nullable=False, default=1)
    max_products = Column(Integer, nullable=False, default=1000)
    max_integrations = Column(Integer, nullable=False, default=1)
    storage_limit_mb = Column(Integer, nullable=False, default=1024)
    is_public = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")
    plan_modules = relationship("PlanModule", back_populates="plan", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<SubscriptionPlan id={self.id} code={self.code!r}>"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="trialing", index=True)
    billing_cycle = Column(String(20), nullable=False, default="monthly")
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    is_auto_renew = Column(Boolean, nullable=False, default=False)
    custom_max_users = Column(Integer, nullable=True)
    custom_max_companies = Column(Integer, nullable=True)
    custom_max_branches = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} tenant_id={self.tenant_id} status={self.status!r}>"


class SystemModule(Base):
    __tablename__ = "system_modules"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(150), nullable=False)
    name_en = Column(String(150), nullable=False)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    is_core = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    plan_modules = relationship("PlanModule", back_populates="module", cascade="all, delete-orphan", passive_deletes=True)
    tenant_modules = relationship("TenantModule", back_populates="module", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<SystemModule id={self.id} code={self.code!r}>"


class PlanModule(Base):
    __tablename__ = "plan_modules"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("system_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    is_enabled = Column(Boolean, nullable=False, default=True)

    plan = relationship("SubscriptionPlan", back_populates="plan_modules")
    module = relationship("SystemModule", back_populates="plan_modules")

    __table_args__ = (UniqueConstraint("plan_id", "module_id", name="uq_plan_module"),)

    def __repr__(self) -> str:
        return f"<PlanModule plan_id={self.plan_id} module_id={self.module_id}>"


class TenantModule(Base):
    __tablename__ = "tenant_modules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("system_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    is_enabled = Column(Boolean, nullable=False, default=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tenant = relationship("Tenant", back_populates="enabled_modules")
    module = relationship("SystemModule", back_populates="tenant_modules")

    __table_args__ = (UniqueConstraint("tenant_id", "module_id", name="uq_tenant_module"),)

    def __repr__(self) -> str:
        return f"<TenantModule tenant_id={self.tenant_id} module_id={self.module_id}>"
