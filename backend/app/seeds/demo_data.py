"""Synthetic multi-tenant evaluation dataset for PrimeERP.

Creates ten isolated demo customers and deterministic master/transaction data.
The seed is idempotent and never modifies the built-in primeerp-demo tenant.

Run:
    python -m app.seeds.demo_data
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.database.models import (
    AuditEvent, EgyptianEInvoiceDocument, ReportDefinition, ReportDelivery, ReportDeliveryAttempt,
    BankAccount, BankStatement, BankStatementLine, ReconciliationSession, ReconciliationMatch,
    InventoryLocation, InventoryTransfer, InventoryTransferLine, InventoryReservation,
    Recipe, RecipeLine, RecipeSkuMapping,
    SallaOrder, SallaOrderItem, SallaCustomer, SallaProduct, SallaProductVariant, SallaShipment, SallaInvoice,
    AccountCombination, AccountingCostCenter, AccountingDepartment, NaturalAccount,
    Branch, BusinessPartner, Budget, BudgetLine, CatalogProduct, Cheque,
    ChequeEvent, Company, Employee, FixedAsset, Floor, IntegrationConnection,
    IntegrationEvent, InventoryItem, InventoryStock, InventoryWarehouse,
    Menu, MenuItem, PayrollLine, PayrollRun, PosMenuItemRoute, PosOutlet,
    PosOutletStation, PosTerminal, PosTerminalMenu, PreparationStation,
    ProductCategory, ProductCostHistory, ProductPrice, ProductPriceList,
    Project, ProjectContract, PurchaseDocument, PurchaseLine, RestaurantTable,
    Role, SalesDocument, SalesLine, ShippingCarrier, ShippingMethod,
    Shipment, Subscription, SubscriptionPlan, SystemModule, Tenant,
    TenantModule, UnitOfMeasure, User, CommercePayment, CommercePaymentAllocation,
    PlanModule,
    CompanyIndustryProfile, LegalDocument, LegalAcceptance, TaxRate, TaxReturnDraft,
    FiscalYear, AccountingPeriod, AccountingJournal, JournalEntry, JournalEntryLine,
    AccountingSettings, NumberSequence, BusinessTransaction, TransactionEvent,
    CommerceAccountingSettings, ShippingSettlementBatch, ShippingShipmentSettlement,
    ShippingPricingProfile, ShippingPricingRule, ShippingShipmentCost, ShippingOrderStatus,
    ShippingStatusHistory, ShippingFinancialEvent, IntegrationMapping, SallaAppInstallation,
    SallaSSOTicket, OrderType, PosOrderLineRoute, InventoryStockMove, InventoryAdjustment,
    InventoryAccountingConfig, InventoryCostLayer, InventoryValuationAllocation,
    Jurisdiction, CompanyJurisdiction, PartnerJurisdiction, TaxRule,
    JurisdictionDecision, TaxSnapshot,
)
from app.database.session import SessionLocal

DEMO_PASSWORD = "Demo@2026!"
TODAY = date(2026, 9, 22)

MODULES = [
    "dashboard", "users", "companies", "branches", "accounting", "sales",
    "inventory", "purchasing", "crm", "restaurant", "pos", "hr",
    "shipping", "manufacturing", "integrations", "reports",
]
MODULE_META = {m: (m.replace("_", " ").title(), m.replace("_", " ").title()) for m in MODULES}
MODULE_META.update({
    "egyptian_einvoice": ("الفاتورة الإلكترونية المصرية", "Egyptian E-Invoice"),
    "helpdesk_ai": ("مساعد الدعم بالذكاء الاصطناعي", "AI Helpdesk"),
    "uom": ("وحدات القياس", "Units of Measure"),
})

CLIENTS = [
    ("demo-nile-hospitality", "Nile Hospitality Group — Demo", "hospitality", "Omar Hassan", "01010000001", "Cairo"),
    ("demo-delta-trading", "Delta Trading & Distribution — Demo", "trading", "Karim Mostafa", "01010000002", "Alexandria"),
    ("demo-cairo-food-retail", "Cairo Food & Retail — Demo", "food_retail", "Ahmed Farouk", "01010000003", "Giza"),
    ("demo-sphinx-manufacturing", "Sphinx Manufacturing Industries — Demo", "manufacturing", "Mina Adel", "01010000004", "10th of Ramadan"),
    ("demo-red-sea-construction", "Red Sea Construction & Projects — Demo", "construction", "Hossam Tarek", "01010000005", "Hurghada"),
    ("demo-capital-real-estate", "Capital Real Estate & Rentals — Demo", "real_estate", "Salma Nabil", "01010000006", "New Cairo"),
    ("demo-medcare-health", "MedCare Clinics & Pharmacy — Demo", "healthcare", "Dina Samir", "01010000007", "Cairo"),
    ("demo-falcon-logistics", "Falcon Logistics & Shipping — Demo", "logistics", "Youssef Adel", "01010000008", "Alexandria"),
    ("demo-smart-tech", "SmartTech Electronics & E-Commerce — Demo", "ecommerce", "Rania Emad", "01010000009", "Cairo"),
    ("demo-nile-agri", "Nile Agro & Food Processing — Demo", "agriculture", "Mahmoud Said", "01010000010", "Dakahlia"),
]

ROLES = {
    "tenant_admin": "Demo tenant administrator",
    "accountant": "Demo accounting user",
    "sales": "Demo sales user",
    "inventory": "Demo inventory user",
    "purchasing": "Demo purchasing user",
    "crm": "Demo CRM user",
    "pos": "Demo POS user",
    "hr": "Demo HR user",
    "operations": "Demo operations user",
}

def get_or_create(db: Session, model, filters: dict, values: dict | None = None):
    obj = db.query(model).filter_by(**filters).first()
    if obj:
        return obj, False
    obj = model(**filters, **(values or {}))
    db.add(obj)
    db.flush()
    return obj, True

def seed_platform(db: Session):
    modules = {}
    for order, code in enumerate(MODULES, 1):
        ar, en = MODULE_META[code]
        obj, _ = get_or_create(
            db, SystemModule, {"code": code},
            {"name_ar": ar, "name_en": en,
             "is_core": code in {"dashboard", "users", "companies", "branches"},
             "is_active": True, "display_order": order},
        )
        modules[code] = obj

    roles = {
        name: get_or_create(db, Role, {"name": name},
                            {"description": description, "is_active": True})[0]
        for name, description in ROLES.items()
    }
    plan, _ = get_or_create(
        db, SubscriptionPlan, {"code": "demo-full-evaluation"},
        {"name_ar": "التقييم الشامل", "name_en": "Full Evaluation Demo",
         "description_ar": "بيانات صناعية مترابطة لتقييم PrimeERP.",
         "description_en": "Synthetic connected data for PrimeERP evaluation.",
         "monthly_price": 0, "yearly_price": 0, "currency_code": "EGP",
         "trial_days": 90, "max_users": 200, "max_companies": 30,
         "max_branches": 150, "max_products": 100000, "max_integrations": 100,
         "storage_limit_mb": 102400, "is_public": False, "is_active": True,
         "display_order": 999},
    )
    for module in modules.values():
        get_or_create(db, PlanModule,
                      {"plan_id": plan.id, "module_id": module.id},
                      {"is_enabled": True})
    return modules, roles, plan

def seed_tenant(db: Session, idx: int, spec, modules, roles, plan):
    slug, name, business_type, owner, phone, city = spec
    email_domain = slug.removeprefix("demo-")
    tenant, _ = get_or_create(
        db, Tenant, {"slug": slug},
        {"name": name, "business_type": business_type, "owner_name": owner,
         "email": f"owner@{email_domain}.demo", "phone": phone,
         "country_code": "EG", "default_language": "ar", "default_locale": "ar-EG",
         "timezone": "Africa/Cairo", "currency_code": "EGP", "status": "active",
         "is_trial": False, "is_active": True},
    )
    now = datetime.now(timezone.utc)
    get_or_create(
        db, Subscription, {"tenant_id": tenant.id, "plan_id": plan.id},
        {"status": "active", "billing_cycle": "yearly", "starts_at": now,
         "ends_at": now + timedelta(days=365), "is_auto_renew": False,
         "notes": "Synthetic evaluation subscription."},
    )
    for module in modules.values():
        get_or_create(db, TenantModule, {"tenant_id": tenant.id, "module_id": module.id},
                      {"is_enabled": True, "starts_at": now})

    companies = []
    for suffix in ("MAIN", "OPS", "SERV"):
        company, _ = get_or_create(
            db, Company, {"tenant_id": tenant.id, "code": f"D{idx:02d}-{suffix}"},
            {"name": f"{name.split(' — ')[0]} {suffix}",
             "description": f"Synthetic {business_type} company",
             "address": f"{city}, Egypt", "phone": phone,
             "email": f"owner@{email_domain}.demo", "is_active": True},
        )
        companies.append(company)

    branches = []
    for bidx, bname in enumerate(
        ["HQ / Administration", "Retail / Sales", "Operations", "Service", "Central Warehouse"], 1
    ):
        company = companies[(bidx - 1) % len(companies)]
        branch, _ = get_or_create(
            db, Branch, {"tenant_id": tenant.id, "company_id": company.id,
                         "code": f"D{idx:02d}-B{bidx:02d}"},
            {"name": f"{bname} — {city}", "address": f"{bname}, {city}, Egypt",
             "phone": phone, "email": f"owner@{email_domain}.demo", "is_active": True},
        )
        branches.append(branch)

    users = []
    role_cycle = ["tenant_admin", "accountant", "sales", "inventory",
                  "purchasing", "crm", "pos", "operations", "hr"]
    for role_name in role_cycle:
        username = f"demo{idx:02d}_{role_name}"
        email = f"{username}@{email_domain}.demo"
        user, _ = get_or_create(
            db, User, {"tenant_id": tenant.id, "username": username},
            {"email": email, "full_name": f"{owner} — {role_name.replace('_', ' ').title()}",
             "phone": phone, "hashed_password": get_password_hash(DEMO_PASSWORD),
             "preferred_language": "ar", "is_active": True,
             "is_superuser": role_name == "tenant_admin", "is_platform_admin": False,
             "is_deleted": False, "must_change_password": False,
             "role_id": roles[role_name].id},
        )
        user.role_id = roles[role_name].id
        users.append(user)
    db.flush()
    return tenant, companies, branches, users

def seed_company_data(db: Session, idx: int, spec, tenant, companies, branches, users):
    company = companies[0]
    company_branches = [b for b in branches if b.company_id == company.id]
    if not company_branches:
        raise RuntimeError(f"No branch belongs to company {company.id} for demo tenant {tenant.id}")
    branch = company_branches[0]
    wh_branch = company_branches[-1]
    stamp = f"D{idx:02d}"
    admin = users[0]
    email_domain = spec[0].removeprefix("demo-")

    unit, _ = get_or_create(db, UnitOfMeasure, {"company_id": company.id, "code": "UNIT"},
                            {"name": "Unit", "category": "count", "factor_to_base": 1,
                             "is_base": True, "is_active": True})
    cat, _ = get_or_create(db, ProductCategory, {"company_id": company.id, "code": f"{stamp}-GEN"},
                           {"name_ar": f"منتجات {idx}", "name_en": f"Products {idx}", "is_active": True})
    wh, _ = get_or_create(
        db, InventoryWarehouse, {"company_id": company.id, "code": f"{stamp}-WH"},
        {"tenant_id": tenant.id, "branch_id": wh_branch.id, "name": f"{spec[1]} Warehouse",
         "description": "Synthetic central warehouse", "is_central": False, "is_active": True},
    )
    price_list, _ = get_or_create(
        db, ProductPriceList, {"company_id": company.id, "code": f"{stamp}-RETAIL"},
        {"name": "Retail EGP", "currency": "EGP", "channel": "retail",
         "is_default": True, "is_active": True},
    )

    items = []
    catalog = []
    for pidx in range(1, 6):
        sku = f"{stamp}-SKU-{pidx:02d}"
        item, _ = get_or_create(
            db, InventoryItem, {"company_id": company.id, "sku": sku},
            {"category_id": cat.id, "barcode": f"628{idx:02d}000{pidx:03d}",
             "name_ar": f"منتج تجريبي {idx}-{pidx}",
             "name_en": f"Demo Product {idx}-{pidx}", "item_type": "stockable",
             "uom": "unit", "uom_id": unit.id, "sales_uom_id": unit.id,
             "purchase_uom_id": unit.id, "sales_tax_ids": [], "purchase_tax_ids": [],
             "costing_method": "fifo", "standard_cost": Decimal(50 + pidx * 10),
             "sales_price": Decimal(100 + pidx * 20),
             "purchase_price": Decimal(50 + pidx * 10), "reorder_level": 10,
             "is_active": True, "description": "Synthetic evaluation item"},
        )
        items.append(item)
        get_or_create(db, InventoryStock,
                      {"company_id": company.id, "item_id": item.id, "warehouse_id": wh.id},
                      {"quantity_on_hand": 100 + pidx * 10, "quantity_reserved": 0,
                       "average_cost": item.standard_cost})
        cp, _ = get_or_create(
            db, CatalogProduct, {"company_id": company.id, "code": f"{stamp}-CP-{pidx:02d}"},
            {"item_id": item.id, "name_ar": item.name_ar, "name_en": item.name_en,
             "product_kind": "traded", "is_sellable": True, "is_active": True},
        )
        catalog.append(cp)
        get_or_create(db, ProductCostHistory,
                      {"company_id": company.id, "product_id": item.id, "cost": item.standard_cost},
                      {"cost_type": "standard", "source": "demo_seed",
                       "note": "Synthetic baseline cost"})
        get_or_create(
            db, ProductPrice,
            {"company_id": company.id, "price_list_id": price_list.id, "product_id": item.id},
            {"catalog_product_id": cp.id, "sale_price": item.sales_price,
             "min_quantity": 1, "source": "demo_seed", "is_active": True},
        )

    customer, _ = get_or_create(
        db, BusinessPartner, {"company_id": company.id, "code": f"{stamp}-CUST-01"},
        {"name": f"Demo Customer {idx}", "partner_type": "customer",
         "tax_number": f"EGTAX{idx:08d}", "phone": f"011200000{idx:02d}",
         "email": f"customer{idx}@{email_domain}.demo", "credit_limit": 50000,
         "payment_terms_days": 30, "is_active": True},
    )
    vendor, _ = get_or_create(
        db, BusinessPartner, {"company_id": company.id, "code": f"{stamp}-VEND-01"},
        {"name": f"Demo Supplier {idx}", "partner_type": "vendor",
         "tax_number": f"EGSUP{idx:08d}", "phone": f"012300000{idx:02d}",
         "email": f"supplier{idx}@{email_domain}.demo", "credit_limit": 0,
         "payment_terms_days": 45, "is_active": True},
    )

    item1, item2 = items[0], items[1]
    sale_total = Decimal("240")
    sale, _ = get_or_create(
        db, SalesDocument, {"company_id": company.id, "number": f"{stamp}-INV-0001"},
        {"partner_id": customer.id, "document_type": "invoice", "document_date": TODAY,
         "due_date": TODAY + timedelta(days=30), "status": "posted", "warehouse_id": wh.id,
         "notes": "Synthetic posted sales invoice", "subtotal": sale_total,
         "tax_total": 0, "discount_total": 0, "total": sale_total, "paid_total": 120},
    )
    sale_line, _ = get_or_create(
        db, SalesLine, {"document_id": sale.id, "item_id": item1.id},
        {"catalog_product_id": catalog[0].id, "quantity": 2, "unit_price": 120,
         "discount_percent": 0, "tax_percent": 0, "line_total": sale_total,
         "tax_rate_ids": []},
    )

    purchase_total = Decimal("120")
    purchase, _ = get_or_create(
        db, PurchaseDocument, {"company_id": company.id, "number": f"{stamp}-BILL-0001"},
        {"partner_id": vendor.id, "document_type": "bill", "document_date": TODAY,
         "due_date": TODAY + timedelta(days=45), "status": "posted", "warehouse_id": wh.id,
         "notes": "Synthetic supplier bill", "subtotal": purchase_total,
         "tax_total": 0, "discount_total": 0, "total": purchase_total, "paid_total": 60},
    )
    get_or_create(
        db, PurchaseLine, {"document_id": purchase.id, "item_id": item2.id},
        {"catalog_product_id": catalog[1].id, "quantity": 2, "unit_price": 60,
         "discount_percent": 0, "tax_percent": 0, "line_total": purchase_total,
         "tax_rate_ids": []},
    )

    pay, _ = get_or_create(
        db, CommercePayment, {"company_id": company.id, "idempotency_key": f"{stamp}-PAY-001"},
        {"document_kind": "sale", "document_id": sale.id, "payment_date": TODAY,
         "amount": 120, "wht_amount": 0, "method": "bank_transfer",
         "reference": f"{stamp}-BANK-001", "status": "posted",
         "notes": "Synthetic customer receipt"},
    )
    get_or_create(
        db, CommercePaymentAllocation,
        {"company_id": company.id, "payment_id": pay.id, "document_kind": "sale",
         "document_id": sale.id},
        {"amount": 120, "status": "active"},
    )

    now = datetime.now(timezone.utc)
    cheque, _ = get_or_create(
        db, Cheque, {"company_id": company.id, "cheque_number": f"{stamp}-CHQ-001"},
        {"partner_id": customer.id, "direction": "received", "bank_name": "Demo Bank",
         "account_number": f"DEMO-{idx:02d}", "cheque_date": TODAY,
         "due_date": TODAY + timedelta(days=15), "amount": 5000, "currency": "EGP",
         "status": "deposited", "notes": "Synthetic treasury cheque",
         "created_at": now, "updated_at": now},
    )
    get_or_create(
        db, ChequeEvent,
        {"company_id": company.id, "cheque_id": cheque.id, "event_type": "deposit"},
        {"from_status": "received", "to_status": "deposited", "event_date": TODAY,
         "reference": f"{stamp}-DEP-001", "created_by": admin.id, "created_at": now},
    )

    employees = []
    for eidx in range(1, 4):
        emp, _ = get_or_create(
            db, Employee, {"company_id": company.id, "employee_no": f"{stamp}-EMP-{eidx:03d}"},
            {"name": f"Demo Employee {idx}-{eidx}",
             "department": ["Finance", "Sales", "Operations"][eidx - 1],
             "job_title": ["Accountant", "Sales Executive", "Operations Officer"][eidx - 1],
             "hire_date": TODAY - timedelta(days=365 + eidx * 30),
             "basic_salary": Decimal(12000 + eidx * 1500), "allowances": Decimal(1500),
             "deductions": Decimal(500), "is_active": True},
        )
        employees.append(emp)
    gross = sum(((e.basic_salary or 0) + (e.allowances or 0)) for e in employees)
    deductions = sum((e.deductions or 0) for e in employees)
    payroll, _ = get_or_create(
        db, PayrollRun, {"company_id": company.id, "period": "2026-09"},
        {"status": "posted", "total_gross": gross, "total_deductions": deductions,
         "total_net": gross - deductions},
    )
    for emp in employees:
        get_or_create(
            db, PayrollLine, {"payroll_run_id": payroll.id, "employee_id": emp.id},
            {"gross": (emp.basic_salary or 0) + (emp.allowances or 0),
             "deductions": emp.deductions or 0,
             "net": (emp.basic_salary or 0) + (emp.allowances or 0) - (emp.deductions or 0)},
        )

    get_or_create(
        db, FixedAsset, {"company_id": company.id, "code": f"{stamp}-AST-001"},
        {"name": "Demo Equipment", "category": "Equipment",
         "acquisition_date": TODAY - timedelta(days=180), "cost": 120000,
         "residual_value": 10000, "useful_life_months": 60,
         "depreciation_method": "straight_line", "accumulated_depreciation": 6000,
         "status": "active"},
    )
    department, _ = get_or_create(
        db, AccountingDepartment,
        {"company_id": company.id, "code": "01"},
        {"name_ar": "الإدارة المالية", "name_en": "Finance", "description": "Synthetic finance department", "is_active": True},
    )
    cost_center, _ = get_or_create(
        db, AccountingCostCenter,
        {"company_id": company.id, "code": "001"},
        {"department_id": department.id, "branch_id": branch.id, "name_ar": "المركز الرئيسي", "name_en": "Main Cost Center", "description": "Synthetic cost center", "is_active": True},
    )
    natural_account, _ = get_or_create(
        db, NaturalAccount,
        {"company_id": company.id, "code": "510"},
        {"name_ar": "مصروفات تشغيلية", "name_en": "Operating Expenses", "financial_statement": "profit_and_loss", "account_category": "expense", "normal_balance": "debit", "level": 1, "is_posting": True, "is_control_account": False, "requires_cost_center": True, "currency_code": "EGP", "is_active": True},
    )
    budget_account, _ = get_or_create(
        db, AccountCombination,
        {"company_id": company.id, "department_id": department.id, "cost_center_id": cost_center.id, "natural_account_id": natural_account.id},
        {"code": "01001510", "name_ar": "مصروفات تشغيلية - المركز الرئيسي", "name_en": "Operating Expenses - Main Cost Center", "opening_debit": 0, "opening_credit": 0, "is_active": True},
    )
    budget, _ = get_or_create(
        db, Budget, {"company_id": company.id, "name": "FY2026 Demo Budget"},
        {"fiscal_year": 2026, "status": "approved", "notes": "Synthetic evaluation budget"},
    )
    get_or_create(db, BudgetLine, {"budget_id": budget.id, "account_id": budget_account.id, "period": 9},
                  {"amount": 250000, "actual_amount": 180000})
    project, _ = get_or_create(
        db, Project, {"company_id": company.id, "code": f"{stamp}-PRJ-001"},
        {"name": f"{spec[1]} Expansion Project",
         "start_date": TODAY - timedelta(days=90), "end_date": TODAY + timedelta(days=180),
         "budget": 500000, "actual_cost": 210000, "status": "active",
         "description": "Synthetic project"},
    )
    get_or_create(
        db, ProjectContract, {"company_id": company.id, "contract_no": f"{stamp}-CON-001"},
        {"project_id": project.id, "customer_id": customer.id, "contract_value": 500000,
         "start_date": project.start_date, "end_date": project.end_date,
         "retention_percent": 5, "status": "active", "terms": "Synthetic contract"},
    )

    carrier, _ = get_or_create(
        db, ShippingCarrier, {"company_id": company.id, "code": f"{stamp}-CARRIER"},
        {"name": f"Demo Carrier {idx}", "api_base_url": "https://carrier.invalid/api",
         "branch_id": branch.id, "is_active": True},
    )
    cod, _ = get_or_create(
        db, ShippingMethod, {"carrier_id": carrier.id, "name": "Demo COD"},
        {"payment_method": "cod", "base_fee": 60, "cod_fee_percent": 2, "estimated_days": 2},
    )
    get_or_create(
        db, Shipment, {"company_id": company.id, "tracking_no": f"{stamp}-TRK-0001"},
        {"carrier_id": carrier.id, "method_id": cod.id, "sales_document_id": sale.id,
         "order_date": TODAY, "shipment_date": TODAY, "zone_code": "CAIRO",
         "weight_kg": 2.5, "pieces": 1, "order_value": sale.total, "cod_amount": 120,
         "cod_collected": 120, "status": "delivered", "shipping_fee": 60,
         "customer_shipping_fee": 60, "customer_name": customer.name, "phone": customer.phone,
         "address": branch.address, "notes": "Synthetic delivered shipment"},
    )

    conn, _ = get_or_create(
        db, IntegrationConnection,
        {"company_id": company.id, "provider": "salla", "name": "Demo Salla"},
        {"base_url": "https://api.salla.dev", "credential_ref": f"demo-credential-{idx}",
         "webhook_secret_env": "PRIMEERP_DEMO_WEBHOOK_SECRET", "is_active": True},
    )
    get_or_create(
        db, IntegrationEvent,
        {"company_id": company.id, "connection_id": conn.id,
         "external_event_id": f"{stamp}-EV-001"},
        {"event_type": "order.created",
         "payload": json.dumps({"demo": True, "order": f"{stamp}-ONLINE-001"}),
         "status": "received", "attempts": 0},
    )

    floor, _ = get_or_create(
        db, Floor, {"branch_id": branch.id, "code": f"{stamp}-F1"},
        {"name": "Main Floor", "description": "Synthetic POS floor",
         "display_order": 1, "is_active": True},
    )
    get_or_create(
        db, RestaurantTable, {"branch_id": branch.id, "code": f"{stamp}-T01"},
        {"floor_id": floor.id, "name": "Table 01", "capacity": 4, "shape": "square",
         "position_x": 10, "position_y": 10, "width": 100, "height": 100,
         "status": "available", "is_active": True},
    )
    station, _ = get_or_create(
        db, PreparationStation, {"branch_id": branch.id, "code": f"{stamp}-KITCHEN"},
        {"name": "Main Kitchen", "station_type": "kitchen", "display_order": 1,
         "is_kds_enabled": True, "is_printer_enabled": False, "is_active": True},
    )
    outlet, _ = get_or_create(
        db, PosOutlet, {"company_id": company.id, "code": f"{stamp}-OUTLET"},
        {"branch_id": branch.id, "warehouse_id": wh.id, "name": "Demo Restaurant Outlet",
         "outlet_type": "restaurant", "is_active": True},
    )
    get_or_create(db, PosOutletStation, {"outlet_id": outlet.id, "station_id": station.id},
                  {"is_active": True})
    terminal, _ = get_or_create(
        db, PosTerminal, {"company_id": company.id, "code": f"{stamp}-POS-01"},
        {"branch_id": branch.id, "outlet_id": outlet.id, "name": "Demo POS 01",
         "device_identifier": f"primeerp-demo-{idx:02d}", "is_active": True},
    )
    menu, _ = get_or_create(
        db, Menu, {"company_id": company.id, "code": f"{stamp}-MENU"},
        {"branch_id": branch.id, "name_ar": "القائمة التجريبية", "name_en": "Demo Menu",
         "description": "Synthetic POS menu", "is_active": True,
         "published_at": datetime.now()},
    )
    for pidx, item in enumerate(items[:3], 1):
        menu_item, _ = get_or_create(
            db, MenuItem, {"menu_id": menu.id, "product_id": item.id},
            {"price_list_id": price_list.id, "sale_price_override": item.sales_price,
             "display_order": pidx, "is_available": True, "is_featured": pidx == 1},
        )
        get_or_create(
            db, PosMenuItemRoute,
            {"terminal_id": terminal.id, "menu_item_id": menu_item.id},
            {"station_id": station.id, "is_active": True},
        )
    get_or_create(db, PosTerminalMenu, {"terminal_id": terminal.id, "menu_id": menu.id},
                  {"price_list_id": price_list.id, "is_active": True})


    # Cross-module evaluation coverage. All records are synthetic and offline.
    receiving, _ = get_or_create(
        db, InventoryLocation,
        {"company_id": company.id, "warehouse_id": wh.id, "code": f"{stamp}-RECV"},
        {"name": "Receiving", "location_type": "receiving", "is_virtual": False, "is_active": True},
    )
    storage, _ = get_or_create(
        db, InventoryLocation,
        {"company_id": company.id, "warehouse_id": wh.id, "code": f"{stamp}-STOR"},
        {"name": "Storage", "location_type": "storage", "is_virtual": False, "is_active": True},
    )
    wh2, _ = get_or_create(
        db, InventoryWarehouse,
        {"company_id": company.id, "code": f"{stamp}-WH2"},
        {"tenant_id": tenant.id, "branch_id": wh_branch.id, "name": f"{spec[1]} Transit Warehouse",
         "description": "Synthetic second warehouse", "is_central": False, "is_active": True},
    )
    transit, _ = get_or_create(
        db, InventoryLocation,
        {"company_id": company.id, "warehouse_id": wh2.id, "code": f"{stamp}-TRANSIT"},
        {"name": "Transit", "location_type": "transit", "is_virtual": False, "is_active": True},
    )
    transfer, _ = get_or_create(
        db, InventoryTransfer,
        {"company_id": company.id, "reference": f"{stamp}-TRF-0001"},
        {"source_warehouse_id": wh.id, "destination_warehouse_id": wh2.id,
         "status": "received", "notes": "Synthetic inventory transfer"},
    )
    get_or_create(
        db, InventoryTransferLine,
        {"transfer_id": transfer.id, "item_id": item1.id},
        {"source_location_id": storage.id, "destination_location_id": transit.id,
         "quantity": 5, "unit_cost": item1.standard_cost,
         "shipped_quantity": 5, "received_quantity": 5},
    )
    get_or_create(
        db, InventoryReservation,
        {"company_id": company.id, "item_id": item1.id, "location_id": storage.id,
         "source_module": "demo", "source_entity": "sales_document", "source_id": str(sale.id)},
        {"quantity": 3, "status": "consumed", "reference": f"{stamp}-RES-0001",
         "notes": "Synthetic reservation lifecycle"},
    )

    recipe, _ = get_or_create(
        db, Recipe,
        {"company_id": company.id, "code": f"{stamp}-REC-001", "version": 1},
        {"product_id": item1.id, "catalog_product_id": catalog[0].id,
         "name_ar": f"وصفة {idx}", "name_en": f"Demo Recipe {idx}",
         "yield_quantity": 1, "waste_percentage": 2, "is_active": True},
    )
    get_or_create(
        db, RecipeLine, {"recipe_id": recipe.id, "line_no": 1},
        {"ingredient_product_id": item2.id, "ingredient_item_id": item2.id,
         "quantity": 1.5, "waste_percentage": 1, "uom_id": unit.id,
         "conversion_factor_to_product_uom": 1, "notes": "Synthetic ingredient"},
    )
    get_or_create(
        db, RecipeSkuMapping,
        {"company_id": company.id, "sku": f"{stamp}-SKU-RECIPE-001"},
        {"recipe_id": recipe.id, "product_id": item1.id,
         "source": "demo",
         "external_id": f"{stamp}-EXT-RECIPE-001", "is_active": True},
    )

    bank, _ = get_or_create(
        db, BankAccount,
        {"company_id": company.id, "name": f"Demo Bank Account {idx}"},
        {"account_combination_id": budget_account.id, "bank_name": "PrimeERP Demo Bank",
         "account_number": f"EG-DEMO-{idx:04d}", "currency": "EGP",
         "opening_balance": 100000, "is_active": True},
    )
    statement, _ = get_or_create(
        db, BankStatement,
        {"bank_account_id": bank.id, "statement_number": f"{stamp}-STMT-001"},
        {"company_id": company.id, "period_start": TODAY.replace(day=1),
         "period_end": TODAY, "opening_balance": 100000,
         "closing_balance": 100120, "status": "closed"},
    )
    stmt_line, _ = get_or_create(
        db, BankStatementLine,
        {"statement_id": statement.id, "fingerprint": f"{stamp}-FP-001"},
        {"company_id": company.id, "external_id": f"{stamp}-EXT-BANK-001",
         "transaction_date": TODAY, "value_date": TODAY,
         "description": "Synthetic customer receipt", "reference": f"{stamp}-BANK-001",
         "debit": 0, "credit": 120, "currency": "EGP",
         "matched_amount": 120, "status": "matched"},
    )
    recon, _ = get_or_create(
        db, ReconciliationSession, {"statement_id": statement.id},
        {"company_id": company.id, "bank_account_id": bank.id,
         "book_balance": 100120, "bank_balance": 100120,
         "difference": 0, "status": "balanced"},
    )
    get_or_create(
        db, ReconciliationMatch,
        {"session_id": recon.id, "source_type": "commerce_payment", "source_id": pay.id},
        {"company_id": company.id, "statement_line_id": stmt_line.id,
         "amount": 120, "created_by": admin.id},
    )


    salla_customer, _ = get_or_create(
        db, SallaCustomer,
        {"connection_id": conn.id, "external_id": f"{stamp}-SCUST-001"},
        {"company_id": company.id, "first_name": "Demo", "last_name": "Customer",
         "mobile": customer.phone, "email": customer.email, "city": spec[5],
         "country": "Egypt", "country_code": "EG", "location": {},
         "urls": {}, "groups": [], "raw_payload": {"demo": True}},
    )
    salla_product, _ = get_or_create(
        db, SallaProduct,
        {"connection_id": conn.id, "external_id": f"{stamp}-SPROD-001"},
        {"company_id": company.id, "sku": item1.sku, "name": item1.name_en,
         "status": "active", "price": item1.sales_price, "taxed_price": item1.sales_price,
         "pre_tax_price": item1.sales_price, "tax": 0, "sale_price": item1.sales_price,
         "cost_price": item1.standard_cost, "quantity": 100, "weight": 1,
         "weight_unit": "kg", "currency": "EGP", "require_shipping": True,
         "is_available": True, "unlimited_quantity": False, "sold_quantity": 0,
         "regular_price": item1.sales_price, "category_ids": [], "brand": {},
         "channels": [], "options": [], "metadata_json": {}, "urls": {}, "images": [],
         "raw_payload": {"demo": True}},
    )
    salla_variant, _ = get_or_create(
        db, SallaProductVariant,
        {"connection_id": conn.id, "external_id": f"{stamp}-SVAR-001"},
        {"company_id": company.id, "product_id": salla_product.id, "sku": item1.sku,
         "barcode": item1.barcode, "price": item1.sales_price,
         "regular_price": item1.sales_price, "cost_price": item1.standard_cost,
         "sale_price": item1.sales_price, "stock": 100, "option_values": [],
         "raw_payload": {"demo": True}},
    )
    salla_order, _ = get_or_create(
        db, SallaOrder,
        {"connection_id": conn.id, "external_id": f"{stamp}-SORDER-001"},
        {"company_id": company.id, "reference_id": f"{stamp}-ONLINE-001",
         "status": "completed", "payment_status": "paid",
         "fulfillment_status": "delivered", "order_type": "online", "currency": "EGP",
         "exchange_rate": 1, "subtotal": sale_total, "discount": 0, "shipping": 60,
         "tax": 0, "total": sale_total + 60, "cod_amount": 0,
         "customer_id": str(salla_customer.external_id), "store_id": f"{stamp}-STORE",
         "urls": {}, "payment_methods": ["card"], "metadata_json": {"demo": True},
         "raw_payload": {"demo": True}, "erp_status": "synced",
         "erp_entity_id": sale.id, "erp_synced_at": now},
    )
    get_or_create(
        db, SallaOrderItem,
        {"connection_id": conn.id, "external_id": f"{stamp}-SOITEM-001"},
        {"company_id": company.id, "order_id": salla_order.id,
         "product_external_id": salla_product.external_id,
         "variant_external_id": salla_variant.external_id, "sku": item1.sku,
         "name": item1.name_en, "quantity": 2, "price": 120, "subtotal": 240,
         "discount": 0, "tax": 0, "total": 240, "cost_price": item1.standard_cost,
         "currency": "EGP", "options": [], "taxes": [], "codes": {}, "urls": {},
         "raw_payload": {"demo": True}},
    )
    get_or_create(
        db, SallaShipment,
        {"connection_id": conn.id, "external_id": f"{stamp}-SSH-001"},
        {"company_id": company.id, "order_id": salla_order.id,
         "order_external_id": salla_order.external_id,
         "order_reference_id": salla_order.reference_id, "shipment_type": "delivery",
         "courier_name": carrier.name, "external_company_name": carrier.name,
         "shipping_number": f"{stamp}-SHIP", "tracking_number": f"{stamp}-TRACK",
         "payment_method": "card", "source": "demo", "status": "delivered",
         "total": 60, "cash_on_delivery": 0, "total_weight": 2.5,
         "international": False, "trackable": True, "packages": [],
         "ship_from": {"city": spec[5]}, "ship_to": {"city": spec[5]},
         "meta": {"demo": True}, "billing_account": {}, "raw_payload": {"demo": True}},
    )
    get_or_create(
        db, SallaInvoice,
        {"connection_id": conn.id, "external_id": f"{stamp}-SINVOICE-001"},
        {"company_id": company.id, "order_id": salla_order.id,
         "invoice_number": f"{stamp}-SINV-0001", "status": "paid",
         "subtotal": 240, "discount": 0, "tax": 0, "shipping": 60, "total": 300,
         "currency": "EGP", "issue_date": TODAY, "due_date": TODAY,
         "urls": {}, "raw_payload": {"demo": True}},
    )

    get_or_create(
        db, AuditEvent,
        {"tenant_id": tenant.id, "company_id": company.id,
         "entity_type": "SalesDocument", "entity_id": str(sale.id), "action": "demo.seed"},
        {"user_id": admin.id, "branch_id": branch.id,
         "request_id": f"{stamp}-REQ-001", "ip_address": "192.0.2.10",
         "user_agent": "PrimeERP-Demo-Seed",
         "metadata_json": json.dumps({"synthetic": True, "module": "sales"})},
    )
    report, _ = get_or_create(
        db, ReportDefinition,
        {"company_id": company.id, "code": f"{stamp}-SALES-DASHBOARD"},
        {"name": "Demo Sales Dashboard", "report_type": "sales",
         "parameters_json": json.dumps({"demo": True}), "is_active": True},
    )
    delivery, _ = get_or_create(
        db, ReportDelivery,
        {"company_id": company.id, "delivery_key": f"{stamp}-REPORT-DELIVERY"},
        {"report_definition_id": report.id, "channel": "email",
         "destination": f"reports@{email_domain}.demo", "schedule": "0 18 * * 0",
         "format": "json", "filters_json": json.dumps({"period": "monthly"}),
         "is_active": True},
    )
    get_or_create(
        db, ReportDeliveryAttempt,
        {"delivery_id": delivery.id, "attempt_no": 1},
        {"status": "success", "response_code": 200,
         "response_reference": f"{stamp}-REPORT-001"},
    )
    get_or_create(
        db, EgyptianEInvoiceDocument,
        {"company_id": company.id, "source_type": "sales_invoice", "source_id": sale.id},
        {"tenant_id": tenant.id, "document_type": "I", "internal_number": sale.number,
         "submission_uuid": f"{stamp}-ETA-SUB-001", "status": "valid",
         "payload_format": "json",
         "signed_payload": json.dumps({"demo": True, "invoice": sale.number}),
         "eta_response": json.dumps({"demo": True, "status": "valid"}),
         "retry_count": 0, "validated_at": datetime.now(timezone.utc)},
    )


    # Full-domain demo workflow coverage. Every persisted domain receives a
    # deterministic lifecycle record scoped to this synthetic tenant/company.
    get_or_create(db, CompanyIndustryProfile, {"company_id": company.id},
                   {"industry_code": spec[2], "business_model": "hybrid",
                    "configuration_json": {"synthetic": True, "industry": spec[2]},
                    "is_active": True})
    get_or_create(db, AccountingSettings, {"company_id": company.id},
                   {"base_currency": "EGP", "code_length": 8, "department_length": 2,
                    "cost_center_length": 3, "natural_account_length": 3,
                    "require_cost_center": True})

    fy, _ = get_or_create(
        db, FiscalYear, {"tenant_id": tenant.id, "company_id": company.id, "code": f"{stamp}-FY26"},
        {"name_ar": f"السنة المالية {idx}", "name_en": f"Demo FY2026 {idx}",
         "start_date": date(2026,1,1), "end_date": date(2026,12,31),
         "status": "open", "is_current": True, "is_adjustment_period_enabled": True,
         "opened_by": admin.id, "opened_at": now, "created_by": admin.id})
    period, _ = get_or_create(
        db, AccountingPeriod, {"fiscal_year_id": fy.id, "period_number": 9},
        {"tenant_id": tenant.id, "company_id": company.id, "code": f"{stamp}-P09",
         "name_ar": "سبتمبر 2026", "name_en": "September 2026",
         "start_date": date(2026,9,1), "end_date": date(2026,9,30),
         "status": "open", "allow_posting": True, "opened_by": admin.id,
         "opened_at": now, "created_by": admin.id})
    journal, _ = get_or_create(
        db, AccountingJournal, {"tenant_id": tenant.id, "company_id": company.id, "code": f"{stamp}-GEN"},
        {"name_ar": "اليومية العامة التجريبية", "name_en": "Demo General Journal",
         "journal_type": "general", "sequence_key": f"{stamp}-JOURNAL_ENTRY",
         "allow_manual_entries": True, "auto_post": False, "requires_approval": True,
         "is_active": True, "created_by": admin.id})
    get_or_create(
        db, NumberSequence,
        {"tenant_id": tenant.id, "company_id": company.id, "branch_id": branch.id,
         "sequence_key": f"{stamp}-JOURNAL_ENTRY"},
        {"prefix": stamp, "format_pattern": "{PREFIX}-{YEAR}-{BRANCH}-{SEQ}",
         "current_value": 1, "padding": 8, "reset_period": "yearly",
         "last_reset_year": 2026, "is_active": True})

    tx, _ = get_or_create(
        db, BusinessTransaction,
        {"tenant_id": tenant.id, "transaction_number": f"{stamp}-TX-0001"},
        {"company_id": company.id, "branch_id": branch.id, "transaction_type": "sales_invoice",
         "document_number": sale.number, "status": "posted", "source_module": "sales",
         "source_entity": "SalesDocument", "source_id": sale.id, "reference_number": sale.number,
         "transaction_date": TODAY, "posting_date": TODAY, "metadata_json": {"synthetic": True},
         "created_by": admin.id, "approved_by": admin.id, "posted_by": admin.id,
         "approved_at": now, "posted_at": now})
    get_or_create(
        db, TransactionEvent,
        {"tenant_id": tenant.id, "transaction_id": tx.id, "event_type": "posted"},
        {"previous_status": "approved", "new_status": "posted",
         "description": "Synthetic transaction posted.", "event_data": {"module": "sales"},
         "performed_by": admin.id})

    entry, _ = get_or_create(
        db, JournalEntry, {"tenant_id": tenant.id, "entry_number": f"{stamp}-JE-0001"},
        {"company_id": company.id, "branch_id": branch.id, "journal_id": journal.id,
         "fiscal_year_id": fy.id, "period_id": period.id, "business_transaction_id": tx.id,
         "entry_date": TODAY, "posting_date": TODAY, "reference": sale.number,
         "description": "Demo balanced sales posting", "currency_code": "EGP",
         "exchange_rate": 1, "total_debit": 240, "total_credit": 240, "status": "posted",
         "source_module": "sales", "source_entity": "SalesDocument", "source_id": sale.id,
         "created_by": admin.id, "posted_by": admin.id, "posted_at": now})
    get_or_create(
        db, JournalEntryLine, {"entry_id": entry.id, "line_number": 1},
        {"tenant_id": tenant.id, "company_id": company.id, "account_combination_id": budget_account.id,
         "department_id": department.id, "cost_center_id": cost_center.id,
         "description": "Demo receivable", "debit": 240, "credit": 0,
         "currency_code": "EGP", "exchange_rate": 1, "base_debit": 240, "base_credit": 0})
    get_or_create(
        db, JournalEntryLine, {"entry_id": entry.id, "line_number": 2},
        {"tenant_id": tenant.id, "company_id": company.id, "account_combination_id": budget_account.id,
         "department_id": department.id, "cost_center_id": cost_center.id,
         "description": "Demo revenue", "debit": 0, "credit": 240,
         "currency_code": "EGP", "exchange_rate": 1, "base_debit": 0, "base_credit": 240})
    get_or_create(
        db, CommerceAccountingSettings, {"company_id": company.id},
        {"sales_journal_id": journal.id, "purchase_journal_id": journal.id,
         "cash_journal_id": journal.id, "ar_account_id": budget_account.id,
         "ap_account_id": budget_account.id, "sales_account_id": budget_account.id,
         "purchase_account_id": budget_account.id, "inventory_account_id": budget_account.id,
         "grni_account_id": budget_account.id, "cogs_account_id": budget_account.id,
         "output_vat_account_id": budget_account.id, "input_vat_account_id": budget_account.id,
         "default_payment_account_id": budget_account.id, "default_branch_id": branch.id,
         "auto_post": True})

    get_or_create(
        db, TaxRate, {"company_id": company.id, "code": f"{stamp}-VAT14"},
        {"name": "VAT 14%", "rate": 14, "tax_type": "vat", "is_withholding": False, "is_active": True})
    get_or_create(
        db, TaxReturnDraft,
        {"company_id": company.id, "period_from": date(2026,9,1), "period_to": date(2026,9,30)},
        {"jurisdiction_code": "EG", "output_vat": 33.6, "input_vat": 16.8, "net_vat": 16.8,
         "is_reconciled": True, "status": "ready", "submission_status": "not_supported",
         "notes": "Synthetic VAT return."})
    eg, _ = get_or_create(
        db, Jurisdiction, {"code": "EG"},
        {"country_code": "EG", "name": "Egypt", "default_currency": "EGP",
         "timezone": "Africa/Cairo", "is_active": True})
    get_or_create(
        db, CompanyJurisdiction,
        {"company_id": company.id, "jurisdiction_id": eg.id, "role": "primary",
         "effective_from": date(2026,1,1)},
        {"tax_resident": True, "vat_registered": True,
         "tax_ids": {"vat": f"EG-VAT-{idx:08d}"}, "is_active": True})
    get_or_create(
        db, PartnerJurisdiction,
        {"partner_id": customer.id, "jurisdiction_id": eg.id, "role": "residence",
         "effective_from": date(2026,1,1)},
        {"tax_resident": True, "vat_registered": False, "tax_ids": {}, "is_active": True})
    rule, _ = get_or_create(
        db, TaxRule,
        {"jurisdiction_id": eg.id, "code": f"{stamp}-VAT-LOCAL", "effective_from": date(2026,1,1)},
        {"name": "Egypt local VAT", "tax_type": "vat", "transaction_type": "sale",
         "taxpayer_type": "both", "place_of_supply": "local", "rate": 14, "priority": 10,
         "conditions": {"demo": True}, "version": "1", "is_active": True})
    decision, _ = get_or_create(
        db, JurisdictionDecision,
        {"company_id": company.id, "jurisdiction_id": eg.id, "transaction_type": "sale",
         "transaction_date": TODAY, "place_of_supply": "local"},
        {"partner_id": customer.id, "b2b": True, "rationale": {"reason": "Demo local sale"},
         "rule_ids": [rule.id]})
    get_or_create(
        db, TaxSnapshot,
        {"company_id": company.id, "document_kind": "sale", "document_id": sale.id},
        {"decision_id": decision.id, "jurisdiction_code": "EG", "country_code": "EG",
         "transaction_date": TODAY, "transaction_type": "sale", "place_of_supply": "local",
         "b2b": True, "facts": {"rate": 14}, "rules": [rule.id]})

    get_or_create(
        db, InventoryAccountingConfig, {"tenant_id": tenant.id, "company_id": company.id},
        {"journal_id": journal.id, "branch_id": branch.id,
         "inventory_account_id": budget_account.id, "cogs_account_id": budget_account.id,
         "adjustment_account_id": budget_account.id, "clearing_account_id": budget_account.id,
         "is_active": "Y"})
    receipt_move, _ = get_or_create(
        db, InventoryStockMove, {"company_id": company.id, "reference": f"{stamp}-RCV-0001"},
        {"item_id": item2.id, "source_location_id": receiving.id, "destination_location_id": storage.id,
         "quantity": 10, "unit_cost": item2.standard_cost, "movement_type": "receipt",
         "status": "draft", "source_module": "purchasing", "source_entity": "PurchaseDocument",
         "source_id": str(purchase.id), "notes": "Demo purchase receipt"})
    layer, _ = get_or_create(
        db, InventoryCostLayer,
        {"company_id": company.id, "item_id": item2.id, "warehouse_id": wh.id, "receipt_move_id": receipt_move.id},
        {"quantity_remaining": 10, "unit_cost": item2.standard_cost})
    move, _ = get_or_create(
        db, InventoryStockMove, {"company_id": company.id, "reference": f"{stamp}-TRN-0001"},
        {"item_id": item1.id, "source_location_id": storage.id, "destination_location_id": transit.id,
         "quantity": 5, "unit_cost": item1.standard_cost, "movement_type": "transfer",
         "status": "posted", "source_module": "inventory", "source_entity": "InventoryTransfer",
         "source_id": str(transfer.id), "notes": "Demo posted transfer"})
    get_or_create(
        db, InventoryValuationAllocation,
        {"company_id": company.id, "stock_move_id": receipt_move.id, "allocation_role": "destination_added"},
        {"cost_layer_id": layer.id, "quantity": 10, "unit_cost": item2.standard_cost})
    get_or_create(
        db, InventoryAdjustment,
        {"company_id": company.id, "item_id": item1.id, "location_id": storage.id,
         "reference": f"{stamp}-ADJ-0001"},
        {"quantity": 2, "direction": "increase", "unit_cost": item1.standard_cost,
         "reason": "Cycle count", "status": "posted", "notes": "Demo adjustment"})

    profile, _ = get_or_create(
        db, ShippingPricingProfile,
        {"company_id": company.id, "carrier_id": carrier.id, "name": f"{stamp}-STANDARD"},
        {"effective_from": date(2026,1,1), "priority": 10, "is_active": True,
         "notes": "Demo pricing profile"})
    get_or_create(
        db, ShippingPricingRule, {"profile_id": profile.id, "priority": 1},
        {"rule_type": "fixed", "basis": "order", "zone_code": "CAIRO",
         "fixed_amount": 60, "included_units": 1, "minimum_amount": 60,
         "is_active": True, "description": "Demo fixed fee"})
    shipment = db.query(Shipment).filter_by(
        company_id=company.id, tracking_no=f"{stamp}-TRK-0001").first()
    get_or_create(
        db, ShippingShipmentCost, {"shipment_id": shipment.id},
        {"profile_id": profile.id, "order_date": TODAY, "shipment_date": TODAY,
         "calculated_at": now, "base_shipping": 60, "cod_fee": 2.4,
         "total_cost": 62.4, "calculation_breakdown": json.dumps({"demo": True})})
    get_or_create(
        db, ShippingOrderStatus, {"company_id": company.id, "code": f"{stamp}-DELIVERED"},
        {"name": "Delivered", "name_ar": "تم التسليم", "sort_order": 50,
         "financial_actions": json.dumps(["collect_cod"]), "allowed_next_codes": "[]", "is_active": True})
    get_or_create(
        db, ShippingStatusHistory, {"shipment_id": shipment.id, "to_status": "delivered"},
        {"from_status": "shipped", "changed_on": TODAY, "note": "Demo delivery"})
    get_or_create(
        db, ShippingFinancialEvent, {"shipment_id": shipment.id, "event_key": f"{stamp}-COD-COLLECTED"},
        {"company_id": company.id, "carrier_id": carrier.id, "event_type": "cod_collected",
         "event_date": TODAY, "amount": 120, "debit_role": "carrier_receivable",
         "credit_role": "cash", "source_status": "delivered", "is_reversal": False,
         "description": "Demo COD collection"})
    batch, _ = get_or_create(
        db, ShippingSettlementBatch,
        {"company_id": company.id, "reference": f"{stamp}-SETTLE-0001"},
        {"carrier_id": carrier.id, "settlement_date": TODAY, "gross_amount": 120,
         "carrier_fees": 62.4, "net_amount": 57.6, "status": "reconciled",
         "notes": "Demo carrier settlement"})
    get_or_create(
        db, ShippingShipmentSettlement, {"batch_id": batch.id, "shipment_id": shipment.id},
        {"expected_amount": 120, "collected_amount": 120, "carrier_fee": 62.4,
         "cod_commission": 2.4, "withdrawal_fee": 0, "other_fee": 0,
         "net_amount": 57.6, "variance": 0, "reconciled": True})

    for code, category, requires_table in (
        ("DINE_IN", "dine_in", True), ("TAKEAWAY", "takeaway", False), ("DELIVERY", "delivery", False)):
        get_or_create(
            db, OrderType, {"branch_id": branch.id, "code": f"{stamp}-{code}"},
            {"name": code.replace("_"," ").title(), "order_category": category,
             "service_charge_percentage": 12 if requires_table else 0,
             "requires_table": requires_table, "requires_customer": category == "delivery",
             "requires_delivery_address": category == "delivery", "display_order": 1, "is_active": True})
    get_or_create(
        db, PosOrderLineRoute, {"sales_line_id": sale_line.id},
        {"terminal_id": terminal.id, "station_id": station.id,
         "status": "completed", "notes": "Demo kitchen route completed"})

    get_or_create(
        db, IntegrationMapping,
        {"company_id": company.id, "connection_id": conn.id, "entity_type": "order",
         "external_id": salla_order.external_id},
        {"local_id": sale.id})
    install, _ = get_or_create(
        db, SallaAppInstallation, {"merchant_id": f"{stamp}-MERCHANT"},
        {"salla_user_id": f"{stamp}-SALLA-USER", "tenant_id": tenant.id, "company_id": company.id,
         "connection_id": conn.id, "user_id": admin.id, "access_token_ciphertext": "demo-access-token",
         "refresh_token_ciphertext": "demo-refresh-token", "scope": "orders products shipments",
         "store_name": f"{spec[1]} Store", "store_domain": f"{email_domain}.salla.demo",
         "merchant_email": f"owner@{email_domain}.demo", "status": "active",
         "subscription_status": "active", "subscription_id": f"{stamp}-SUB",
         "trial_ends_at": now + timedelta(days=30), "last_authorized_at": now,
         "last_webhook_at": now, "metadata_json": {"synthetic": True}})
    get_or_create(
        db, SallaSSOTicket, {"id": f"{stamp}-SSO-TICKET-0001"},
        {"installation_id": install.id, "tenant_id": tenant.id, "user_id": admin.id,
         "expires_at": now + timedelta(minutes=10)})

    legal, _ = get_or_create(
        db, LegalDocument, {"document_type": f"demo-terms-{idx}"},
        {"title_ar": "شروط الاستخدام التجريبية", "title_en": "Demo Terms of Use",
         "content_ar": "وثيقة تجريبية.", "content_en": "Synthetic terms.",
         "version": 1, "is_published": True, "published_at": now, "updated_by": admin.id})
    get_or_create(
        db, LegalAcceptance,
        {"user_id": admin.id, "document_type": legal.document_type, "document_version": legal.version},
        {"accepted_at": now})

    return sale.id, purchase.id


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        modules, roles, plan = seed_platform(db)
        results = []
        for idx, spec in enumerate(CLIENTS, 1):
            tenant, companies, branches, users = seed_tenant(db, idx, spec, modules, roles, plan)
            sale_id, purchase_id = seed_company_data(
                db, idx, spec, tenant, companies, branches, users
            )
            results.append((tenant, sale_id, purchase_id))
        db.commit()
        print("PrimeERP synthetic evaluation dataset created/verified.")
        print(f"Clients: {len(results)} | Companies: {len(results) * 3} | Branches: {len(results) * 5} | Users: {len(results) * 9}")
        print(f"Enabled modules per client: {len(modules)}")
        print(f"Demo password: {DEMO_PASSWORD}")
        for tenant, sale_id, purchase_id in results:
            print(f"- {tenant.slug}: tenant_id={tenant.id}, sale_id={sale_id}, purchase_id={purchase_id}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
