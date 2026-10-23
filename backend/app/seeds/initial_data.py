"""Safe, idempotent bootstrap for system modules and subscription plans.

This command intentionally does not create user accounts, credentials, demo
tenants, companies, branches, or subscriptions. Tenant creation belongs to the
validated SaaS registration flow.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.database.models import PlanModule, SubscriptionPlan, SystemModule
from app.database.session import SessionLocal


SYSTEM_MODULES = [
    {
        "code": "dashboard",
        "name_ar": "لوحة التحكم",
        "name_en": "Dashboard",
        "is_core": True,
        "display_order": 1,
    },
    {
        "code": "users",
        "name_ar": "المستخدمون",
        "name_en": "Users",
        "is_core": True,
        "display_order": 2,
    },
    {
        "code": "companies",
        "name_ar": "الشركات",
        "name_en": "Companies",
        "is_core": True,
        "display_order": 3,
    },
    {
        "code": "branches",
        "name_ar": "الفروع",
        "name_en": "Branches",
        "is_core": True,
        "display_order": 4,
    },
    {
        "code": "accounting",
        "name_ar": "الحسابات",
        "name_en": "Accounting",
        "is_core": False,
        "display_order": 10,
    },
    {
        "code": "sales",
        "name_ar": "المبيعات",
        "name_en": "Sales",
        "is_core": False,
        "display_order": 20,
    },
    {
        "code": "inventory",
        "name_ar": "المخزون",
        "name_en": "Inventory",
        "is_core": False,
        "display_order": 30,
    },
    {
        "code": "purchasing",
        "name_ar": "المشتريات",
        "name_en": "Purchasing",
        "is_core": False,
        "display_order": 40,
    },
    {
        "code": "crm",
        "name_ar": "إدارة العملاء",
        "name_en": "CRM",
        "is_core": False,
        "display_order": 50,
    },
    {
        "code": "restaurant",
        "name_ar": "إدارة المطاعم",
        "name_en": "Restaurant",
        "is_core": False,
        "display_order": 60,
    },
    {
        "code": "pos",
        "name_ar": "نقاط البيع",
        "name_en": "Point of Sale",
        "is_core": False,
        "display_order": 70,
    },
    {
        "code": "hr",
        "name_ar": "الموارد البشرية",
        "name_en": "Human Resources",
        "is_core": False,
        "display_order": 80,
    },
    {
        "code": "shipping",
        "name_ar": "شركات الشحن",
        "name_en": "Shipping",
        "is_core": False,
        "display_order": 90,
    },
    {
        "code": "manufacturing",
        "name_ar": "التصنيع",
        "name_en": "Manufacturing",
        "is_core": False,
        "display_order": 100,
    },
    {
        "code": "integrations",
        "name_ar": "التكاملات",
        "name_en": "Integrations",
        "is_core": False,
        "display_order": 110,
    },
    {
        "code": "reports",
        "name_ar": "التقارير",
        "name_en": "Reports",
        "is_core": False,
        "display_order": 120,
    },
]


PLANS = [
    {
        "code": "trial",
        "name_ar": "الباقة التجريبية",
        "name_en": "Trial",
        "monthly_price": Decimal("0"),
        "yearly_price": Decimal("0"),
        "trial_days": 14,
        "max_users": 5,
        "max_companies": 1,
        "max_branches": 2,
        "max_products": 1000,
        "max_integrations": 1,
        "storage_limit_mb": 1024,
        "is_public": False,
        "display_order": 0,
        "modules": [
            "dashboard",
            "users",
            "companies",
            "branches",
            "accounting",
            "sales",
            "inventory",
            "restaurant",
            "pos",
            "reports",
        ],
    },
    {
        "code": "starter",
        "name_ar": "الباقة الأساسية",
        "name_en": "Starter",
        "monthly_price": Decimal("999"),
        "yearly_price": Decimal("9990"),
        "trial_days": 14,
        "max_users": 10,
        "max_companies": 1,
        "max_branches": 3,
        "max_products": 5000,
        "max_integrations": 2,
        "storage_limit_mb": 5120,
        "is_public": True,
        "display_order": 1,
        "modules": [
            "dashboard",
            "users",
            "companies",
            "branches",
            "accounting",
            "sales",
            "inventory",
            "purchasing",
            "crm",
            "reports",
        ],
    },
    {
        "code": "professional",
        "name_ar": "الباقة الاحترافية",
        "name_en": "Professional",
        "monthly_price": Decimal("2499"),
        "yearly_price": Decimal("24990"),
        "trial_days": 14,
        "max_users": 30,
        "max_companies": 3,
        "max_branches": 10,
        "max_products": 50000,
        "max_integrations": 10,
        "storage_limit_mb": 20480,
        "is_public": True,
        "display_order": 2,
        "modules": [
            module["code"]
            for module in SYSTEM_MODULES
        ],
    },
]


def get_or_create_system_module(
    db: Session,
    module_data: dict,
) -> SystemModule:
    module = (
        db.query(SystemModule)
        .filter(
            SystemModule.code
            == module_data["code"]
        )
        .first()
    )

    if module:
        return module

    module = SystemModule(
        code=module_data["code"],
        name_ar=module_data["name_ar"],
        name_en=module_data["name_en"],
        is_core=module_data["is_core"],
        is_active=True,
        display_order=module_data["display_order"],
    )

    db.add(module)
    db.flush()

    return module


def get_or_create_plan(
    db: Session,
    plan_data: dict,
    modules_by_code: dict[str, SystemModule],
) -> SubscriptionPlan:
    plan = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.code
            == plan_data["code"]
        )
        .first()
    )

    if not plan:
        plan = SubscriptionPlan(
            code=plan_data["code"],
            name_ar=plan_data["name_ar"],
            name_en=plan_data["name_en"],
            monthly_price=plan_data[
                "monthly_price"
            ],
            yearly_price=plan_data[
                "yearly_price"
            ],
            currency_code="EGP",
            trial_days=plan_data[
                "trial_days"
            ],
            max_users=plan_data["max_users"],
            max_companies=plan_data[
                "max_companies"
            ],
            max_branches=plan_data[
                "max_branches"
            ],
            max_products=plan_data[
                "max_products"
            ],
            max_integrations=plan_data[
                "max_integrations"
            ],
            storage_limit_mb=plan_data[
                "storage_limit_mb"
            ],
            is_public=plan_data["is_public"],
            is_active=True,
            display_order=plan_data[
                "display_order"
            ],
        )

        db.add(plan)
        db.flush()

    existing_module_ids = {
        item.module_id
        for item in plan.plan_modules
    }

    for module_code in plan_data["modules"]:
        module = modules_by_code[module_code]

        if module.id in existing_module_ids:
            existing = next(item for item in plan.plan_modules if item.module_id == module.id)
            existing.is_enabled = True
            continue

        db.add(
            PlanModule(
                plan_id=plan.id,
                module_id=module.id,
                is_enabled=True,
            )
        )

    db.flush()

    return plan


def seed_initial_data() -> None:
    db = SessionLocal()

    try:
        modules_by_code: dict[
            str,
            SystemModule,
        ] = {}

        for module_data in SYSTEM_MODULES:
            module = get_or_create_system_module(
                db,
                module_data,
            )

            modules_by_code[
                module.code
            ] = module

        plans_by_code: dict[
            str,
            SubscriptionPlan,
        ] = {}

        for plan_data in PLANS:
            plan = get_or_create_plan(
                db,
                plan_data,
                modules_by_code,
            )

            plans_by_code[
                plan.code
            ] = plan

        db.commit()

        print("PrimeERP system bootstrap completed successfully.")
        print(f"System modules configured: {len(modules_by_code)}")
        print(f"Subscription plans configured: {len(plans_by_code)}")
        print("No user accounts, demo tenants, companies, branches, or subscriptions were created.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_initial_data()