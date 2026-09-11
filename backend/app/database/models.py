"""
Central SQLAlchemy model registry.

Importing this module registers all models in Base.metadata.
Do not define SQLAlchemy models directly in this file.
"""

from app.modules.saas.models import (
    PlanModule, Subscription, SubscriptionPlan, SystemModule, Tenant, TenantModule,
)
from app.modules.platform.plans.models import Plan
from app.modules.platform.customers.models import Customer
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.identity.models.user import User
from app.modules.roles.models import Permission, Role, role_permissions
from app.modules.legal.models import LegalAcceptance, LegalDocument
from app.modules.restaurant.models import Floor, OrderType, PreparationStation, RestaurantTable
from app.modules.accounting.chart_of_accounts.models import (
    AccountCombination, AccountingCostCenter, AccountingDepartment, AccountingSettings, NaturalAccount,
)
from app.modules.transactions.models import BusinessTransaction, NumberSequence, TransactionEvent
from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.accounting.journals.models import AccountingJournal, JournalEntry, JournalEntryLine
from app.modules.inventory.items.models import InventoryItem, InventoryStock
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.location_stock import InventoryLocationStock
from app.modules.inventory.transfers.models import InventoryTransfer, InventoryTransferLine
from app.modules.inventory.adjustments.models import InventoryAdjustment
from app.modules.inventory.reservations.models import InventoryReservation
from app.modules.purchasing.suppliers.models import Supplier
from app.modules.purchasing.purchase_orders.models import PurchaseOrder, PurchaseOrderLine
from app.modules.sales.sales_core.models import SalesOrder

__all__ = [
    "Tenant", "SubscriptionPlan", "Subscription", "SystemModule", "PlanModule", "TenantModule",
    "Plan", "Customer", "Company", "Branch", "User", "Role", "Permission", "role_permissions",
    "LegalDocument", "LegalAcceptance", "Floor", "RestaurantTable", "PreparationStation", "OrderType",
    "AccountingDepartment", "AccountingCostCenter", "NaturalAccount", "AccountCombination", "AccountingSettings",
    "NumberSequence", "BusinessTransaction", "TransactionEvent", "FiscalYear", "AccountingPeriod",
    "AccountingJournal", "JournalEntry", "JournalEntryLine", "InventoryItem", "InventoryStock",
    "InventoryWarehouse", "InventoryLocation", "InventoryStockMove", "InventoryLocationStock",
    "InventoryTransfer", "InventoryTransferLine", "InventoryAdjustment", "InventoryReservation",
    "Supplier", "PurchaseOrder", "PurchaseOrderLine", "SalesOrder",
]
