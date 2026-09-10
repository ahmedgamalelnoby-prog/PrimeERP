"""Central SQLAlchemy model registry.

Importing this module registers all models in Base.metadata.
Do not define SQLAlchemy models directly in this file.
"""
from app.modules.saas.models import PlanModule, Subscription, SubscriptionPlan, SystemModule, Tenant, TenantModule
from app.modules.platform.plans.models import Plan
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.identity.models.user import User
from app.modules.roles.models import Permission, Role, role_permissions
from app.modules.legal.models import LegalAcceptance, LegalDocument
from app.modules.restaurant.models import Floor, OrderType, PreparationStation, RestaurantTable
from app.modules.accounting.chart_of_accounts.models import AccountCombination, AccountingCostCenter, AccountingDepartment, AccountingSettings, NaturalAccount
from app.modules.transactions.models import BusinessTransaction, NumberSequence, TransactionEvent
from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.accounting.journals.models import AccountingJournal, JournalEntry, JournalEntryLine
from app.modules.shipping.models import ShippingPaymentProfile, ShippingProvider, ShippingProviderService, ShippingRateCard, Shipment, ShipmentEvent, ShippingSettlement

__all__ = [
    "Tenant", "SubscriptionPlan", "Subscription", "SystemModule", "PlanModule", "TenantModule", "Plan", "Company", "Branch", "User", "Role", "Permission", "role_permissions", "LegalDocument", "LegalAcceptance", "Floor", "RestaurantTable", "PreparationStation", "OrderType", "AccountingDepartment", "AccountingCostCenter", "NaturalAccount", "AccountCombination", "AccountingSettings", "NumberSequence", "BusinessTransaction", "TransactionEvent", "FiscalYear", "AccountingPeriod", "AccountingJournal", "JournalEntry", "JournalEntryLine", "ShippingProvider", "ShippingProviderService", "ShippingPaymentProfile", "ShippingRateCard", "Shipment", "ShipmentEvent", "ShippingSettlement",
]
