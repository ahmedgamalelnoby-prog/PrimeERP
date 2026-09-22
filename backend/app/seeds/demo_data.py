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
)
from app.database.session import SessionLocal

DEMO_PASSWORD = "Demo@2026!"
TODAY = date(2026, 9, 22)

MODULES = [
    "dashboard", "users", "companies", "branches", "accounting", "audit",
    "catalog", "commerce", "commissions", "crm", "developer",
    "egyptian_einvoice", "enterprise", "helpdesk_ai", "hr", "installments",
    "integrations", "inventory", "jurisdiction", "legal", "loyalty",
    "manufacturing", "mobile", "notifications", "operations", "organization",
    "platform", "pos", "promotions", "purchasing", "reports", "rentals",
    "restaurant", "roles", "saas", "sales", "settings", "shipping",
    "subscriptions", "taxes", "transactions", "treasury", "uom",
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
                  "purchasing", "crm", "operations", "hr"]
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
    branch = branches[1]
    wh_branch = branches[4]
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
    budget, _ = get_or_create(
        db, Budget, {"company_id": company.id, "name": "FY2026 Demo Budget"},
        {"fiscal_year": 2026, "status": "approved", "notes": "Synthetic evaluation budget"},
    )
    get_or_create(db, BudgetLine, {"budget_id": budget.id, "account_id": 1, "period": 9},
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
        print(f"Clients: {len(results)} | Companies: {len(results) * 3} | Branches: {len(results) * 5} | Users: {len(results) * 8}")
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
