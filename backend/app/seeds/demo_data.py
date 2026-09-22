"""Deterministic multi-tenant demo dataset for PrimeERP evaluation.

This seed is intentionally synthetic and idempotent. It creates three independent
client tenants, companies, branches, users, roles, subscriptions, and enables every
registered PrimeERP module for each demo tenant.

Run from backend:
    python -m app.seeds.demo_data

The script never touches the existing PrimeERP demo tenant.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.database.models import (
    Branch,
    Company,
    PlanModule,
    Role,
    Subscription,
    SubscriptionPlan,
    SystemModule,
    Tenant,
    TenantModule,
    User,
)
from app.database.session import SessionLocal


DEMO_PASSWORD = "Demo@2026!"

# Keep this list aligned with the actual module packages in backend/app/modules.
# Core platform modules are included as well so the demo tenants exercise
# entitlement and navigation across the complete product surface.
ALL_MODULES = [
    "dashboard", "users", "companies", "branches", "accounting", "audit",
    "catalog", "commerce", "commissions", "crm", "dashboard", "developer",
    "egyptian_einvoice", "enterprise", "helpdesk_ai", "hr", "installments",
    "integrations", "inventory", "jurisdiction", "legal", "loyalty",
    "manufacturing", "mobile", "notifications", "operations", "organization",
    "platform", "pos", "promotions", "purchasing", "reports", "rentals",
    "restaurant", "roles", "saas", "sales", "settings", "shipping",
    "subscriptions", "taxes", "transactions", "treasury", "uom",
]

# Human-facing metadata for modules that may not already exist in SystemModule.
MODULE_META = {
    "audit": ("المراجعة", "Audit"),
    "catalog": ("دليل المنتجات", "Catalog"),
    "commerce": ("التجارة الإلكترونية", "Commerce"),
    "commissions": ("العمولات", "Commissions"),
    "developer": ("المطور", "Developer"),
    "egyptian_einvoice": ("الفاتورة الإلكترونية المصرية", "Egyptian E-Invoice"),
    "enterprise": ("المؤسسات", "Enterprise"),
    "helpdesk_ai": ("مساعد الدعم بالذكاء الاصطناعي", "AI Helpdesk"),
    "installments": ("التقسيط", "Installments"),
    "jurisdiction": ("الاختصاص الضريبي", "Jurisdiction"),
    "legal": ("الشؤون القانونية", "Legal"),
    "loyalty": ("الولاء", "Loyalty"),
    "mobile": ("تطبيق الهاتف", "Mobile"),
    "notifications": ("الإشعارات", "Notifications"),
    "operations": ("العمليات", "Operations"),
    "organization": ("الهيكل التنظيمي", "Organization"),
    "platform": ("المنصة", "Platform"),
    "promotions": ("العروض", "Promotions"),
    "rentals": ("الإيجارات", "Rentals"),
    "roles": ("الأدوار والصلاحيات", "Roles"),
    "saas": ("إدارة الاشتراكات", "SaaS"),
    "settings": ("الإعدادات", "Settings"),
    "subscriptions": ("الاشتراكات", "Subscriptions"),
    "taxes": ("الضرائب", "Taxes"),
    "transactions": ("المعاملات", "Transactions"),
    "treasury": ("الخزينة", "Treasury"),
    "uom": ("وحدات القياس", "Units of Measure"),
}

CLIENTS = [
    ("nile-hospitality", "Nile Hospitality Group — Demo", "hospitality", "Omar Hassan", "01010000001", "Cairo"),
    ("delta-trading", "Delta Trading & Distribution — Demo", "trading", "Karim Mostafa", "01010000002", "Alexandria"),
    ("cairo-food-retail", "Cairo Food & Retail — Demo", "food_retail", "Ahmed Farouk", "01010000003", "Giza"),
    ("sphinx-manufacturing", "Sphinx Manufacturing Industries — Demo", "manufacturing", "Mina Adel", "01010000004", "10th of Ramadan"),
    ("red-sea-construction", "Red Sea Construction & Projects — Demo", "construction", "Hossam Tarek", "01010000005", "Hurghada"),
    ("capital-real-estate", "Capital Real Estate & Rentals — Demo", "real_estate", "Salma Nabil", "01010000006", "New Cairo"),
    ("medcare-health", "MedCare Clinics & Pharmacy — Demo", "healthcare", "Dina Samir", "01010000007", "Cairo"),
    ("falcon-logistics", "Falcon Logistics & Shipping — Demo", "logistics", "Youssef Adel", "01010000008", "Alexandria"),
    ("smart-tech", "SmartTech Electronics & E-Commerce — Demo", "ecommerce", "Rania Emad", "01010000009", "Cairo"),
    ("nile-agri", "Nile Agro & Food Processing — Demo", "agriculture", "Mahmoud Said", "01010000010", "Dakahlia"),
]"""Deterministic multi-tenant demo dataset for PrimeERP evaluation.

This seed is intentionally synthetic and idempotent. It creates three independent
client tenants, companies, branches, users, roles, subscriptions, and enables every
registered PrimeERP module for each demo tenant.

Run from backend:
    python -m app.seeds.demo_data

The script never touches the existing PrimeERP demo tenant.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.database.models import (
    Branch,
    Company,
    PlanModule,
    Role,
    Subscription,
    SubscriptionPlan,
    SystemModule,
    Tenant,
    TenantModule,
    User,
)
from app.database.session import SessionLocal


DEMO_PASSWORD = "Demo@2026!"

# Keep this list aligned with the actual module packages in backend/app/modules.
# Core platform modules are included as well so the demo tenants exercise
# entitlement and navigation across the complete product surface.
ALL_MODULES = [
    "dashboard", "users", "companies", "branches", "accounting", "audit",
    "catalog", "commerce", "commissions", "crm", "dashboard", "developer",
    "egyptian_einvoice", "enterprise", "helpdesk_ai", "hr", "installments",
    "integrations", "inventory", "jurisdiction", "legal", "loyalty",
    "manufacturing", "mobile", "notifications", "operations", "organization",
    "platform", "pos", "promotions", "purchasing", "reports", "rentals",
    "restaurant", "roles", "saas", "sales", "settings", "shipping",
    "subscriptions", "taxes", "transactions", "treasury", "uom",
]

# Human-facing metadata for modules that may not already exist in SystemModule.
MODULE_META = {
    "audit": ("المراجعة", "Audit"),
    "catalog": ("دليل المنتجات", "Catalog"),
    "commerce": ("التجارة الإلكترونية", "Commerce"),
    "commissions": ("العمولات", "Commissions"),
    "developer": ("المطور", "Developer"),
    "egyptian_einvoice": ("الفاتورة الإلكترونية المصرية", "Egyptian E-Invoice"),
    "enterprise": ("المؤسسات", "Enterprise"),
    "helpdesk_ai": ("مساعد الدعم بالذكاء الاصطناعي", "AI Helpdesk"),
    "installments": ("التقسيط", "Installments"),
    "jurisdiction": ("الاختصاص الضريبي", "Jurisdiction"),
    "legal": ("الشؤون القانونية", "Legal"),
    "loyalty": ("الولاء", "Loyalty"),
    "mobile": ("تطبيق الهاتف", "Mobile"),
    "notifications": ("الإشعارات", "Notifications"),
    "operations": ("العمليات", "Operations"),
    "organization": ("الهيكل التنظيمي", "Organization"),
    "platform": ("المنصة", "Platform"),
    "promotions": ("العروض", "Promotions"),
    "rentals": ("الإيجارات", "Rentals"),
    "roles": ("الأدوار والصلاحيات", "Roles"),
    "saas": ("إدارة الاشتراكات", "SaaS"),
    "settings": ("الإعدادات", "Settings"),
    "subscriptions": ("الاشتراكات", "Subscriptions"),
    "taxes": ("الضرائب", "Taxes"),
    "transactions": ("المعاملات", "Transactions"),
    "treasury": ("الخزينة", "Treasury"),
    "uom": ("وحدات القياس", "Units of Measure"),
}

CLIENTS = [
    {
        "slug": "demo-nile-hospitality",
        "name": "Nile Hospitality Group — Demo",
        "business_type": "hospitality",
        "owner": "Omar Hassan",
        "email": "owner@nile-hospitality.demo",
        "phone": "01010000001",
        "companies": [
            ("NHG", "Nile Hospitality Company"),
            ("NHG-FNB", "Nile Hospitality Food & Beverage"),
        ],
        "branches": [
            ("NHG-CEN", "Cairo Central Office"),
            ("NHG-HOT", "Nile View Hotel"),
            ("NHG-RES", "Nile View Restaurant"),
            ("NHG-NC", "North Coast Resort"),
        ],
        "users": [
            ("admin", "admin@nile-hospitality.demo", "Omar Hassan", "tenant_admin"),
            ("finance", "finance@nile-hospitality.demo", "Mariam Adel", "accountant"),
            ("sales", "sales@nile-hospitality.demo", "Youssef Ali", "sales"),
            ("inventory", "inventory@nile-hospitality.demo", "Hany Samir", "inventory"),
            ("pos", "pos@nile-hospitality.demo", "Salma Nabil", "pos"),
            ("hr", "hr@nile-hospitality.demo", "Nada Fathy", "hr"),
        ],
    },
    {
        "slug": "demo-delta-trading",
        "name": "Delta Trading & Distribution — Demo",
        "business_type": "trading",
        "owner": "Karim Mostafa",
        "email": "owner@delta-trading.demo",
        "phone": "01010000002",
        "companies": [
            ("DTG", "Delta Trading Company"),
            ("DTG-DIST", "Delta Distribution Company"),
        ],
        "branches": [
            ("DTG-HQ", "Alexandria Head Office"),
            ("DTG-CAR", "Cairo Distribution Center"),
            ("DTG-ALEX", "Alexandria Sales Branch"),
            ("DTG-TAN", "Tanta Sales Branch"),
        ],
        "users": [
            ("admin", "admin@delta-trading.demo", "Karim Mostafa", "tenant_admin"),
            ("finance", "finance@delta-trading.demo", "Rania Emad", "accountant"),
            ("sales", "sales@delta-trading.demo", "Mahmoud Ashraf", "sales"),
            ("purchasing", "purchasing@delta-trading.demo", "Dina Wael", "purchasing"),
            ("warehouse", "warehouse@delta-trading.demo", "Tarek Said", "inventory"),
            ("crm", "crm@delta-trading.demo", "Aya Khaled", "crm"),
        ],
    },
    {
        "slug": "demo-cairo-food-retail",
        "name": "Cairo Food & Retail — Demo",
        "business_type": "food_retail",
        "owner": "Ahmed Farouk",
        "email": "owner@cairo-food.demo",
        "phone": "01010000003",
        "companies": [
            ("CFR", "Cairo Food Retail Company"),
            ("CFR-KIT", "Cairo Central Kitchen"),
        ],
        "branches": [
            ("CFR-ZAM", "Zamalek Store"),
            ("CFR-OCT", "6 October Store"),
            ("CFR-MAD", "Maadi Store"),
            ("CFR-KIT", "Central Kitchen"),
        ],
        "users": [
            ("admin", "admin@cairo-food.demo", "Ahmed Farouk", "tenant_admin"),
            ("finance", "finance@cairo-food.demo", "Heba Sameh", "accountant"),
            ("store1", "store1@cairo-food.demo", "Mostafa Reda", "store_manager"),
            ("store2", "store2@cairo-food.demo", "Mai Hassan", "store_manager"),
            ("pos", "pos@cairo-food.demo", "Nour Tamer", "pos"),
            ("operations", "operations@cairo-food.demo", "Sherif Wael", "operations"),
        ],
    },
]


def get_or_create_module(db: Session, code: str, order: int) -> SystemModule:
    module = db.query(SystemModule).filter(SystemModule.code == code).first()
    if module:
        return module

    name_ar, name_en = MODULE_META.get(
        code,
        (code.replace("_", " ").title(), code.replace("_", " ").title()),
    )
    module = SystemModule(
        code=code,
        name_ar=name_ar,
        name_en=name_en,
        is_core=code in {"dashboard", "users", "companies", "branches"},
        is_active=True,
        display_order=order,
    )
    db.add(module)
    db.flush()
    return module


def get_or_create_role(db: Session, name: str, description: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name, description=description, is_active=True)
    db.add(role)
    db.flush()
    return role


def get_or_create_professional_plan(
    db: Session,
    modules: dict[str, SystemModule],
) -> SubscriptionPlan:
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.code == "demo-professional"
    ).first()
    if not plan:
        plan = SubscriptionPlan(
            code="demo-professional",
            name_ar="باقة التقييم الشاملة",
            name_en="Full Evaluation Demo",
            description_ar="بيانات وهمية لاختبار جميع وحدات PrimeERP.",
            description_en="Synthetic dataset for evaluating the complete PrimeERP surface.",
            monthly_price=0,
            yearly_price=0,
            currency_code="EGP",
            trial_days=90,
            max_users=100,
            max_companies=20,
            max_branches=100,
            max_products=100000,
            max_integrations=100,
            storage_limit_mb=102400,
            is_public=False,
            is_active=True,
            display_order=99,
        )
        db.add(plan)
        db.flush()

    existing = {x.module_id for x in plan.plan_modules}
    for module in modules.values():
        if module.id not in existing:
            db.add(PlanModule(plan_id=plan.id, module_id=module.id, is_enabled=True))
    db.flush()
    return plan


def seed_client(
    db: Session,
    spec: dict,
    plan: SubscriptionPlan,
    modules: dict[str, SystemModule],
    roles: dict[str, Role],
) -> dict:
    now = datetime.now(timezone.utc)
    tenant = db.query(Tenant).filter(Tenant.slug == spec["slug"]).first()

    if not tenant:
        tenant = Tenant(
            name=spec["name"],
            slug=spec["slug"],
            business_type=spec["business_type"],
            owner_name=spec["owner"],
            email=spec["email"],
            phone=spec["phone"],
            country_code="EG",
            default_language="ar",
            default_locale="ar-EG",
            timezone="Africa/Cairo",
            currency_code="EGP",
            status="active",
            is_trial=False,
            is_active=True,
        )
        db.add(tenant)
        db.flush()

    subscription = db.query(Subscription).filter(
        Subscription.tenant_id == tenant.id,
        Subscription.plan_id == plan.id,
    ).first()
    if not subscription:
        subscription = Subscription(
            tenant_id=tenant.id,
            plan_id=plan.id,
            status="active",
            billing_cycle="yearly",
            starts_at=now,
            ends_at=now + timedelta(days=365),
            trial_ends_at=None,
            is_auto_renew=False,
            notes="Synthetic demo subscription for product evaluation.",
        )
        db.add(subscription)

    enabled = {x.module_id for x in tenant.enabled_modules}
    for module in modules.values():
        if module.id not in enabled:
            db.add(
                TenantModule(
                    tenant_id=tenant.id,
                    module_id=module.id,
                    is_enabled=True,
                    starts_at=now,
                    ends_at=None,
                )
            )

    companies = []
    for code, name in spec["companies"]:
        company = db.query(Company).filter(
            Company.tenant_id == tenant.id,
            Company.code == code,
        ).first()
        if not company:
            company = Company(
                tenant_id=tenant.id,
                name=name,
                code=code,
                description=f"Synthetic company for {spec['name']}",
                address="Egypt",
                phone=spec["phone"],
                email=spec["email"],
                is_active=True,
            )
            db.add(company)
            db.flush()
        companies.append(company)

    branches = []
    for idx, (code, name) in enumerate(spec["branches"]):
        company = companies[idx % len(companies)]
        branch = db.query(Branch).filter(
            Branch.tenant_id == tenant.id,
            Branch.company_id == company.id,
            Branch.code == code,
        ).first()
        if not branch:
            branch = Branch(
                tenant_id=tenant.id,
                company_id=company.id,
                name=name,
                code=code,
                address=f"{name}, Egypt",
                phone=spec["phone"],
                email=spec["email"],
                is_active=True,
            )
            db.add(branch)
            db.flush()
        branches.append(branch)

    users = []
    for username, email, full_name, role_name in spec["users"]:
        role = roles[role_name]
        user = db.query(User).filter(
            User.tenant_id == tenant.id,
            User.username == username,
        ).first()
        if not user:
            user = User(
                tenant_id=tenant.id,
                username=username,
                email=email,
                full_name=full_name,
                phone=spec["phone"],
                hashed_password=get_password_hash(DEMO_PASSWORD),
                preferred_language="ar",
                is_active=True,
                is_superuser=role_name == "tenant_admin",
                is_platform_admin=False,
                is_deleted=False,
                must_change_password=False,
                role_id=role.id,
            )
            db.add(user)
        else:
            user.role_id = role.id
            user.is_active = True
            user.is_deleted = False
        users.append(user)

    db.flush()
    return {
        "tenant": tenant,
        "companies": companies,
        "branches": branches,
        "users": users,
    }


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        modules: dict[str, SystemModule] = {}
        for order, code in enumerate(dict.fromkeys(ALL_MODULES), start=1):
            modules[code] = get_or_create_module(db, code, order)

        roles = {
            name: get_or_create_role(db, name, description)
            for name, description in {
                "tenant_admin": "Demo tenant administrator",
                "accountant": "Demo accounting user",
                "sales": "Demo sales user",
                "inventory": "Demo inventory user",
                "purchasing": "Demo purchasing user",
                "crm": "Demo CRM user",
                "pos": "Demo POS user",
                "hr": "Demo HR user",
                "store_manager": "Demo store manager",
                "operations": "Demo operations user",
            }.items()
        }

        plan = get_or_create_professional_plan(db, modules)
        results = [seed_client(db, spec, plan, modules, roles) for spec in CLIENTS]

        db.commit()

        print("PrimeERP synthetic evaluation dataset created/verified.")
        print(f"Clients: {len(results)}")
        print("Each client: 2 companies, 4 branches, 6 users.")
        print(f"Enabled modules per client: {len(modules)}")
        print(f"Demo password for all generated users: {DEMO_PASSWORD}")
        for item in results:
            tenant = item["tenant"]
            print(f"- {tenant.slug}: tenant_id={tenant.id}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
