"""Central SQLAlchemy model registry."""
from app.modules.identity.models.user import User
from app.modules.identity.models.refresh_token import RefreshToken
from app.modules.saas.models import PlanModule, Subscription, SubscriptionPlan, SystemModule, Tenant, TenantModule
from app.modules.platform.plans.models import Plan
from app.modules.companies.models import Company
from app.modules.companies.industry_models import CompanyIndustryProfile
from app.modules.branches.models import Branch
from app.modules.roles.models import Permission, Role, role_permissions
from app.modules.legal.models import LegalAcceptance, LegalDocument
from app.modules.audit.models import AuditEvent
from app.modules.egyptian_einvoice.models import EgyptianEInvoiceDocument
from app.modules.reports.models import ReportDefinition, ReportDelivery, ReportDeliveryAttempt
from app.modules.restaurant.models import Floor, OrderType, PreparationStation, RestaurantTable, PosOutlet, PosOutletStation, PosTerminal, PosTerminalMenu, PosMenuItemRoute, PosOrderLineRoute
from app.modules.accounting.chart_of_accounts.models import AccountCombination, AccountingCostCenter, AccountingDepartment, AccountingSettings, NaturalAccount
from app.modules.transactions.models import BusinessTransaction, NumberSequence, TransactionEvent
from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.accounting.journals.models import AccountingJournal, JournalEntry, JournalEntryLine
from app.modules.accounting.models import TaxRate
from app.modules.taxes.models import TaxReturnDraft
from app.modules.inventory.items.models import InventoryItem, InventoryStock
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove, InventoryCostLayer
from app.modules.inventory.stock_moves.location_stock import InventoryLocationStock
from app.modules.inventory.transfers.models import InventoryTransfer, InventoryTransferLine
from app.modules.inventory.adjustments.models import InventoryAdjustment
from app.modules.inventory.reservations.models import InventoryReservation
from app.modules.commerce.models import BusinessPartner, SalesDocument, SalesLine, PurchaseDocument, PurchaseLine, CommercePayment, CommercePaymentAllocation, PurchaseBillReceiptLink, PurchaseBillReceiptAllocation
from app.modules.commerce.sales_return_models import SalesReturnAllocation
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.enterprise.models import FixedAsset, Budget, BudgetLine, Employee, PayrollRun, PayrollLine, Project, ProjectContract
from app.modules.shipping.models import ShippingCarrier, ShippingMethod, Shipment
from app.modules.shipping.settlement_models import ShippingSettlementBatch, ShippingShipmentSettlement
from app.modules.shipping.pricing_models import ShippingPricingProfile, ShippingPricingRule
from app.modules.shipping.cost_models import ShippingShipmentCost
from app.modules.shipping.status_models import ShippingOrderStatus, ShippingStatusHistory, ShippingFinancialEvent
from app.modules.integrations.models import IntegrationConnection, IntegrationEvent, IntegrationMapping
from app.modules.integrations.salla_public_app_models import SallaAppInstallation, SallaSSOTicket
from app.modules.integrations.salla_models import SallaOrder, SallaOrderItem, SallaCustomer, SallaProduct, SallaProductVariant, SallaShipment, SallaInvoice
from app.modules.uom.models import UnitOfMeasure
from app.modules.treasury.models import Cheque, ChequeEvent
from app.modules.treasury.bank_reconciliation.models import BankAccount, BankStatement, BankStatementLine, ReconciliationSession, ReconciliationMatch
from app.modules.catalog.models import CatalogProduct, ProductCategory, ProductPriceList, ProductPrice, ProductCostHistory, Recipe, RecipeLine, RecipeSkuMapping, Menu, MenuItem
from app.modules.jurisdiction.models import Jurisdiction, CompanyJurisdiction, PartnerJurisdiction, TaxRule, JurisdictionDecision, TaxSnapshot
from app.modules.ai_reporting.models import ReportSchedule, ReportDeliveryLog
from app.modules.completion.models import FunctionalTransaction, TransactionApproval, PostingDiagnostic, ReconciliationItem, PeriodControl
from app.modules.accounting.automation_models import JournalAutomation, JournalAllocation
from app.modules.accounting.advanced_models import AccountingAutoPostRule, AccountingFXRevaluation, AccountingIntercompanyLink, AccountingElimination, AccountingPostingLink
from app.modules.accounting.recognition_models import AccountingRecognitionSchedule
from app.modules.accounting.fiscal_years.models.close_control import FiscalYearCloseChecklistItem, FiscalYearCloseRun, FiscalYearCloseAudit
from app.modules.completion.enterprise_models import DomainControl, WorkflowRule, MasterDataIdentity, AIActionAudit, SubscriptionUsage
from app.modules.completion.finance_models import SettlementAllocation, ReturnControl, IntegrationDelivery
from app.modules.completion.domain_models import FinanceAgingSnapshot, FinanceWriteOff, FinanceReconciliation, InventoryTraceUnit, ManufacturingWorkOrder, ManufacturingConsumption, CRMOpportunity, CRMActivity, HRAttendance, HRLeave, HRPayrollCompletionRun, TaxFilingControl, SubscriptionLifecycleEvent, APIClientCredential, WebhookDeliveryControl, MobileSyncQueue, WorkflowInstance, WorkflowApprovalStep

__all__ = ['Tenant','SubscriptionPlan','Subscription','SystemModule','PlanModule','TenantModule','Plan','Company','CompanyIndustryProfile','Branch','User','RefreshToken','Role','Permission','role_permissions','LegalDocument','LegalAcceptance','AuditEvent','EgyptianEInvoiceDocument','ReportDefinition','ReportDelivery','ReportDeliveryAttempt','TaxReturnDraft','Floor','RestaurantTable','PreparationStation','OrderType','AccountingDepartment','AccountingCostCenter','NaturalAccount','AccountCombination','AccountingSettings','NumberSequence','BusinessTransaction','TransactionEvent','FiscalYear','AccountingPeriod','AccountingJournal','JournalEntry','JournalEntryLine','TaxRate','InventoryItem','InventoryStock','InventoryWarehouse','InventoryLocation','InventoryStockMove','InventoryLocationStock','InventoryTransfer','InventoryTransferLine','InventoryAdjustment','InventoryReservation','BusinessPartner','SalesDocument','SalesLine','PurchaseDocument','PurchaseLine','CommercePayment','CommercePaymentAllocation','PurchaseBillReceiptLink','PurchaseBillReceiptAllocation','SalesReturnAllocation','CommerceAccountingSettings','FixedAsset','Budget','BudgetLine','Employee','PayrollRun','PayrollLine','Project','ProjectContract','ShippingCarrier','ShippingMethod','Shipment','ShippingSettlementBatch','ShippingShipmentSettlement','ShippingPricingProfile','ShippingPricingRule','ShippingShipmentCost','ShippingOrderStatus','ShippingStatusHistory','ShippingFinancialEvent','IntegrationConnection','IntegrationEvent','IntegrationMapping','SallaAppInstallation','SallaSSOTicket','SallaOrder','SallaOrderItem','SallaCustomer','SallaProduct','SallaProductVariant','SallaShipment','SallaInvoice','UnitOfMeasure','ReportSchedule','ReportDeliveryLog','Cheque','ChequeEvent','BankAccount','BankStatement','BankStatementLine','ReconciliationSession','ReconciliationMatch','CatalogProduct','ProductCategory','ProductPriceList','ProductPrice','ProductCostHistory','Recipe','RecipeLine','Menu','MenuItem','Jurisdiction','CompanyJurisdiction','PartnerJurisdiction','TaxRule','JurisdictionDecision','TaxSnapshot','FunctionalTransaction','TransactionApproval','PostingDiagnostic','ReconciliationItem','PeriodControl','JournalAutomation','JournalAllocation','AccountingAutoPostRule','AccountingFXRevaluation','AccountingIntercompanyLink','AccountingElimination','AccountingPostingLink','AccountingRecognitionSchedule','InventoryCostLayer','DomainControl','WorkflowRule','MasterDataIdentity','AIActionAudit','SubscriptionUsage','SettlementAllocation','ReturnControl','IntegrationDelivery']

from app.modules.commerce.ar_models import ARWriteOff, ARReconciliation
