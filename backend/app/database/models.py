"""
Central SQLAlchemy model registry.

Importing this module registers all models in Base.metadata.
Do not define SQLAlchemy models directly in this file.
"""

# SaaS models are imported first because other models
# contain foreign keys referencing the tenants table.
from app.modules.saas.models import (
    PlanModule,
    Subscription,
    SubscriptionPlan,
    SystemModule,
    Tenant,
    TenantModule,
)

# Platform models.
from app.modules.platform.plans.models import Plan

# Organization models.
from app.modules.companies.models import Company
from app.modules.branches.models import Branch

# Identity models.
# User lives exclusively in the identity module. The legacy
# app.modules.auth.models.User duplicate has been removed so SQLAlchemy
# has a single authoritative mapper for the users table.
from app.modules.identity.models.user import User
from app.modules.roles.models import (
    Permission,
    Role,
    role_permissions,
)

# Restaurant models.
from app.modules.restaurant.models import (
    Floor,
    OrderType,
    PreparationStation,
    RestaurantTable,
)

# Accounting models.
from app.modules.accounting.chart_of_accounts.models import (
    AccountCombination,
    AccountingCostCenter,
    AccountingDepartment,
    AccountingSettings,
    NaturalAccount,
)

from app.modules.transactions.models import (
    BusinessTransaction,
    NumberSequence,
    TransactionEvent,
)

from app.modules.accounting.fiscal_years.models import (
    AccountingPeriod,
    FiscalYear,
)

from app.modules.accounting.journals.models import (
    AccountingJournal,
    JournalEntry,
    JournalEntryLine,
)

__all__ = [
    # SaaS
    "Tenant",
    "SubscriptionPlan",
    "Subscription",
    "SystemModule",
    "PlanModule",
    "TenantModule",

    # Platform
    "Plan",

    # Organization
    "Company",
    "Branch",

    # Identity
    "User",
    "Role",
    "Permission",
    "role_permissions",

    # Restaurant
    "Floor",
    "RestaurantTable",
    "PreparationStation",
    "OrderType",

    # Accounting
    "AccountingDepartment",
    "AccountingCostCenter",
    "NaturalAccount",
    "AccountCombination",
    "AccountingSettings",
    "NumberSequence",
    "BusinessTransaction",
    "TransactionEvent",
    "FiscalYear",
    "AccountingPeriod",
    "AccountingJournal",
    "JournalEntry",
    "JournalEntryLine",
]
