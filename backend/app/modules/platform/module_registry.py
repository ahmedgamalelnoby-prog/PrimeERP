from __future__ import annotations

from typing import Literal

ModuleStatus = Literal["active", "foundation", "roadmap"]

MODULE_REGISTRY: tuple[dict[str, object], ...] = (
    {"key": "accounting", "name": "Accounting", "name_ar": "المحاسبة", "group": "finance", "status": "active", "description": "General ledger, journals, fiscal periods, chart of accounts and financial reporting."},
    {"key": "treasury", "name": "Treasury", "name_ar": "الخزينة والبنوك", "group": "finance", "status": "active", "description": "Cash, banks, cheques, collections and payment lifecycle controls."},
    {"key": "taxes", "name": "Taxes", "name_ar": "الضرائب", "group": "finance", "status": "active", "description": "Tax master data, rates and tax controls."},
    {"key": "einvoice", "name": "Egyptian E-Invoice", "name_ar": "الفاتورة الإلكترونية المصرية", "group": "finance", "status": "active", "description": "Egyptian e-invoice integration and compliance workflow."},
    {"key": "inventory", "name": "Inventory", "name_ar": "المخزون", "group": "operations", "status": "active", "description": "Items, warehouses, locations, stock moves, transfers, reservations, adjustments and costing."},
    {"key": "catalog", "name": "Product Catalog", "name_ar": "كتالوج المنتجات", "group": "operations", "status": "active", "description": "Products, variants, bundles, UOM and pricing."},
    {"key": "sales", "name": "Sales", "name_ar": "المبيعات", "group": "commercial", "status": "active", "description": "Customers, quotations, orders, deliveries, invoices, returns and payments."},
    {"key": "purchasing", "name": "Purchasing", "name_ar": "المشتريات", "group": "commercial", "status": "foundation", "description": "Supplier and purchase lifecycle foundation integrated with commerce."},
    {"key": "commerce", "name": "Commerce", "name_ar": "التجارة", "group": "commercial", "status": "active", "description": "Commercial documents, partners, payments and operational lifecycle."},
    {"key": "shipping", "name": "Shipping", "name_ar": "الشحن", "group": "operations", "status": "active", "description": "Shipping operations, settlement and accounting integration."},
    {"key": "enterprise", "name": "Enterprise", "name_ar": "إدارة المؤسسة", "group": "enterprise", "status": "active", "description": "Enterprise operational capabilities, assets, budgets, HR, projects and contracts."},
    {"key": "identity", "name": "Identity & Access", "name_ar": "الهوية والصلاحيات", "group": "platform", "status": "active", "description": "Authentication, users, roles, permissions and tenant-aware access."},
    {"key": "organization", "name": "Organization", "name_ar": "المؤسسة والفروع", "group": "platform", "status": "active", "description": "Companies, branches and organizational structure."},
    {"key": "saas", "name": "SaaS", "name_ar": "إدارة SaaS", "group": "platform", "status": "active", "description": "Plans, subscriptions, trials and module entitlements."},
    {"key": "integrations", "name": "Integrations", "name_ar": "التكاملات", "group": "platform", "status": "active", "description": "External providers, product mappings, reliable events and integrations."},
    {"key": "audit", "name": "Audit", "name_ar": "سجل التدقيق", "group": "platform", "status": "active", "description": "Audit trail and operational traceability."},
    {"key": "legal", "name": "Legal", "name_ar": "الشؤون القانونية", "group": "enterprise", "status": "active", "description": "Legal documents, policies and public legal pages."},
    {"key": "reports", "name": "Reports & Analytics", "name_ar": "التقارير والتحليلات", "group": "intelligence", "status": "active", "description": "Financial reporting, AI analysis and scheduled delivery."},
    {"key": "helpdesk", "name": "AI Help Desk", "name_ar": "الدعم الفني بالذكاء الاصطناعي", "group": "intelligence", "status": "active", "description": "Product-aware AI guidance and business assistance."},
    {"key": "uom", "name": "Units of Measure", "name_ar": "وحدات القياس", "group": "operations", "status": "active", "description": "Units and conversion rules."},
    {"key": "commissions", "name": "Commissions", "name_ar": "العمولات", "group": "commercial", "status": "active", "description": "Commission rules and calculations."},
    {"key": "subscriptions", "name": "Subscriptions", "name_ar": "الاشتراكات", "group": "commercial", "status": "foundation", "description": "Recurring subscription lifecycle."},
    {"key": "pos", "name": "POS", "name_ar": "نقطة البيع", "group": "commercial", "status": "foundation", "description": "Point-of-sale foundation."},
    {"key": "restaurant", "name": "Restaurant", "name_ar": "المطاعم", "group": "industry", "status": "foundation", "description": "Restaurant operational foundation."},
    {"key": "hospitality", "name": "Hospitality", "name_ar": "الضيافة والفنادق", "group": "industry", "status": "roadmap", "description": "Hotel operations, revenue and profit-share workflows."},
    {"key": "commercial_leasing", "name": "Commercial Leasing", "name_ar": "الإيجارات التجارية", "group": "industry", "status": "roadmap", "description": "Commercial lease contracts, installments and revenue share."},
    {"key": "real_estate", "name": "Real Estate", "name_ar": "العقارات", "group": "industry", "status": "foundation", "description": "Real-estate operational foundation."},
    {"key": "crm", "name": "CRM", "name_ar": "إدارة العملاء", "group": "commercial", "status": "foundation", "description": "Leads, opportunities and customer pipeline foundation."},
    {"key": "projects", "name": "Projects", "name_ar": "المشروعات", "group": "enterprise", "status": "foundation", "description": "Projects, tasks and milestones foundation."},
    {"key": "documents", "name": "Documents", "name_ar": "المستندات", "group": "enterprise", "status": "foundation", "description": "Document management foundation."},
    {"key": "contracts", "name": "Contracts", "name_ar": "العقود", "group": "enterprise", "status": "foundation", "description": "Contract lifecycle foundation."},
    {"key": "notifications", "name": "Notifications", "name_ar": "الإشعارات", "group": "platform", "status": "foundation", "description": "Notification delivery foundation."},
    {"key": "workflow", "name": "Workflow", "name_ar": "سير العمل", "group": "platform", "status": "foundation", "description": "Approval and workflow foundation."},
    {"key": "approvals", "name": "Approvals", "name_ar": "الموافقات", "group": "platform", "status": "foundation", "description": "Approval workflow foundation."},
    {"key": "assets", "name": "Assets", "name_ar": "الأصول", "group": "finance", "status": "foundation", "description": "Fixed asset lifecycle foundation."},
    {"key": "expenses", "name": "Expenses", "name_ar": "المصروفات", "group": "finance", "status": "foundation", "description": "Expense management foundation."},
    {"key": "budgets", "name": "Budgets", "name_ar": "الموازنات", "group": "finance", "status": "foundation", "description": "Budgeting foundation."},
    {"key": "manufacturing", "name": "Manufacturing", "name_ar": "التصنيع", "group": "operations", "status": "roadmap", "description": "Manufacturing and production planning."},
    {"key": "quality", "name": "Quality", "name_ar": "الجودة", "group": "operations", "status": "roadmap", "description": "Quality control workflows."},
    {"key": "maintenance", "name": "Maintenance", "name_ar": "الصيانة", "group": "operations", "status": "roadmap", "description": "Maintenance workflows."},
    {"key": "work_orders", "name": "Work Orders", "name_ar": "أوامر العمل", "group": "operations", "status": "foundation", "description": "Work order foundation."},
    {"key": "loyalty", "name": "Loyalty", "name_ar": "ولاء العملاء", "group": "commercial", "status": "roadmap", "description": "Customer loyalty programs."},
    {"key": "promotions", "name": "Promotions", "name_ar": "العروض", "group": "commercial", "status": "roadmap", "description": "Promotion and pricing campaigns."},
    {"key": "rentals", "name": "Rentals", "name_ar": "التأجير", "group": "industry", "status": "foundation", "description": "Rental lifecycle foundation."},
)

REGISTRY_VERSION = "2026.09.18.1"


def list_modules() -> list[dict[str, object]]:
    return [dict(item) for item in MODULE_REGISTRY]


def get_module(module_key: str) -> dict[str, object] | None:
    return next((dict(item) for item in MODULE_REGISTRY if item["key"] == module_key), None)


def knowledge_context() -> str:
    return "\n".join(
        f"- {item['name']} ({item['name_ar']}): {item['status']}. {item['description']}"
        for item in MODULE_REGISTRY
    )
