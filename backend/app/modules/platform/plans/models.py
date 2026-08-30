from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.database.base import Base

from app.core.database.mixins import (
    SoftDeleteMixin,
    TimestampMixin,
    UUIDMixin,
)

from app.modules.platform.plans.constants import (
    DEFAULT_GRACE_PERIOD_DAYS,
    DEFAULT_PLAN_CURRENCY,
    DEFAULT_SORT_ORDER,
    DEFAULT_TRIAL_DAYS,
    BillingCycle,
    PlanStatus,
    PlanType,
)


class Plan(
    Base,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "plans"

    __table_args__ = (
        UniqueConstraint(
            "code",
            "version",
            name="uq_plan_code_version",
        ),
        CheckConstraint(
            "monthly_price >= 0",
            name="ck_plan_monthly_price",
        ),
        CheckConstraint(
            "yearly_price >= 0",
            name="ck_plan_yearly_price",
        ),
        CheckConstraint(
            "trial_days >= 0",
            name="ck_plan_trial_days",
        ),
        CheckConstraint(
            "grace_period_days >= 0",
            name="ck_plan_grace_period_days",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_plan_version",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_plan_sort_order",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    version = Column(
        Integer,
        nullable=False,
        default=1,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    name_ar = Column(
        String(100),
        nullable=True,
    )

    display_name = Column(
        String(100),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    monthly_price = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )

    yearly_price = Column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )

    currency = Column(
        String(10),
        nullable=False,
        default=DEFAULT_PLAN_CURRENCY.value,
    )

    billing_cycle = Column(
        String(20),
        nullable=False,
        default=BillingCycle.MONTHLY.value,
    )

    trial_days = Column(
        Integer,
        nullable=False,
        default=DEFAULT_TRIAL_DAYS,
    )

    grace_period_days = Column(
        Integer,
        nullable=False,
        default=DEFAULT_GRACE_PERIOD_DAYS,
    )

    effective_from = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    effective_to = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_default = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_public = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_free = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_custom = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    status = Column(
        String(20),
        nullable=False,
        default=PlanStatus.DRAFT.value,
        index=True,
    )

    plan_type = Column(
        String(30),
        nullable=False,
        default=PlanType.STANDARD.value,
        index=True,
    )

    sort_order = Column(
        Integer,
        nullable=False,
        default=DEFAULT_SORT_ORDER,
    )

    def __repr__(self) -> str:
        return (
            f"<Plan("
            f"id={self.id}, "
            f"code='{self.code}', "
            f"version={self.version}, "
            f"name='{self.name}', "
            f"status='{self.status}'"
            f")>"
        )