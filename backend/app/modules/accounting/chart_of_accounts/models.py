from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class AccountingDepartment(Base):
    """
    الإدارة التي تمثل أول رقمين من الكود المحاسبي.

    مثال:
    01 = الإدارة المالية
    02 = التشغيل
    03 = الموارد البشرية
    """

    __tablename__ = "accounting_departments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    code = Column(
        String(2),
        nullable=False,
    )

    name_ar = Column(
        String(150),
        nullable=False,
    )

    name_en = Column(
        String(150),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cost_centers = relationship(
        "AccountingCostCenter",
        back_populates="department",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    account_combinations = relationship(
        "AccountCombination",
        back_populates="department",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_accounting_department_company_code",
        ),
        CheckConstraint(
            "char_length(code) = 2",
            name="ck_accounting_department_code_length",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountingDepartment "
            f"{self.code} - {self.name_ar}>"
        )


class AccountingCostCenter(Base):
    """
    مركز التكلفة الذي يمثل الثلاثة أرقام الوسطى.

    مثال:
    005 = الإدارة المالية
    120 = فرع المطعم
    """

    __tablename__ = "accounting_cost_centers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    department_id = Column(
        Integer,
        ForeignKey(
            "accounting_departments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    branch_id = Column(
        Integer,
        ForeignKey(
            "branches.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    code = Column(
        String(3),
        nullable=False,
    )

    name_ar = Column(
        String(150),
        nullable=False,
    )

    name_en = Column(
        String(150),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    department = relationship(
        "AccountingDepartment",
        back_populates="cost_centers",
    )

    account_combinations = relationship(
        "AccountCombination",
        back_populates="cost_center",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_accounting_cost_center_company_code",
        ),
        CheckConstraint(
            "char_length(code) = 3",
            name="ck_accounting_cost_center_code_length",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountingCostCenter "
            f"{self.code} - {self.name_ar}>"
        )


class NaturalAccount(Base):
    """
    الحساب الطبيعي، ويمثل آخر ثلاثة أرقام.

    هذا هو الحساب الأساسي في الشجرة:
    أصول، خصوم، إيرادات، مصروفات...
    """

    __tablename__ = "natural_accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    parent_id = Column(
        Integer,
        ForeignKey(
            "natural_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    code = Column(
        String(3),
        nullable=False,
    )

    name_ar = Column(
        String(200),
        nullable=False,
    )

    name_en = Column(
        String(200),
        nullable=True,
    )

    financial_statement = Column(
        String(30),
        nullable=False,
    )

    account_category = Column(
        String(50),
        nullable=False,
    )

    normal_balance = Column(
        String(10),
        nullable=False,
    )

    level = Column(
        Integer,
        default=1,
        nullable=False,
    )

    is_posting = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_control_account = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    requires_cost_center = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    currency_code = Column(
        String(3),
        default="EGP",
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    parent = relationship(
        "NaturalAccount",
        remote_side=[id],
        back_populates="children",
    )

    children = relationship(
        "NaturalAccount",
        back_populates="parent",
    )

    account_combinations = relationship(
        "AccountCombination",
        back_populates="natural_account",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "code",
            name="uq_natural_account_company_code",
        ),
        CheckConstraint(
            "char_length(code) = 3",
            name="ck_natural_account_code_length",
        ),
        CheckConstraint(
            "financial_statement IN "
            "('balance_sheet', 'profit_and_loss')",
            name="ck_natural_account_statement",
        ),
        CheckConstraint(
            "normal_balance IN ('debit', 'credit')",
            name="ck_natural_account_normal_balance",
        ),
        CheckConstraint(
            "level >= 1",
            name="ck_natural_account_level",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NaturalAccount "
            f"{self.code} - {self.name_ar}>"
        )


class AccountCombination(Base):
    """
    الكود المحاسبي النهائي المكوّن من 8 أرقام.

    Department + Cost Center + Natural Account

    مثال:
    01 + 005 + 101 = 01005101
    """

    __tablename__ = "account_combinations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    department_id = Column(
        Integer,
        ForeignKey(
            "accounting_departments.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    cost_center_id = Column(
        Integer,
        ForeignKey(
            "accounting_cost_centers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    natural_account_id = Column(
        Integer,
        ForeignKey(
            "natural_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    code = Column(
        String(8),
        nullable=False,
        index=True,
    )

    name_ar = Column(
        String(250),
        nullable=False,
    )

    name_en = Column(
        String(250),
        nullable=True,
    )

    opening_debit = Column(
        Numeric(18, 2),
        default=0,
        nullable=False,
    )

    opening_credit = Column(
        Numeric(18, 2),
        default=0,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    department = relationship(
        "AccountingDepartment",
        back_populates="account_combinations",
    )

    cost_center = relationship(
        "AccountingCostCenter",
        back_populates="account_combinations",
    )

    natural_account = relationship(
        "NaturalAccount",
        back_populates="account_combinations",
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "department_id",
            "cost_center_id",
            "natural_account_id",
            name="uq_account_combination_dimensions",
        ),
        CheckConstraint(
            "char_length(code) = 8",
            name="ck_account_combination_code_length",
        ),
        CheckConstraint(
            "opening_debit >= 0",
            name="ck_account_combination_opening_debit",
        ),
        CheckConstraint(
            "opening_credit >= 0",
            name="ck_account_combination_opening_credit",
        ),
        CheckConstraint(
            "NOT (opening_debit > 0 AND opening_credit > 0)",
            name="ck_account_combination_single_opening_side",
        ),
        Index(
            "ix_account_combination_company_active",
            "company_id",
            "is_active",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountCombination "
            f"{self.code} - {self.name_ar}>"
        )


class AccountingSettings(Base):
    """
    إعدادات الحسابات لكل شركة.
    """

    __tablename__ = "accounting_settings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    code_format = Column(
        String(50),
        default="department_cost_center_account",
        nullable=False,
    )

    code_length = Column(
        Integer,
        default=8,
        nullable=False,
    )

    department_length = Column(
        Integer,
        default=2,
        nullable=False,
    )

    cost_center_length = Column(
        Integer,
        default=3,
        nullable=False,
    )

    natural_account_length = Column(
        Integer,
        default=3,
        nullable=False,
    )

    base_currency = Column(
        String(3),
        default="EGP",
        nullable=False,
    )

    allow_manual_code = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    allow_duplicate_account_names = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    require_cost_center = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )