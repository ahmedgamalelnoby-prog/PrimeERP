"""Seed the PrimeERP application catalog against the Odoo 19 module surface.

This is an architectural parity layer, not a copy of Odoo source code.  PrimeERP
keeps its own FastAPI/SQLAlchemy implementation while exposing a complete,
installable ERP application catalog so SaaS plans and tenant entitlements can
be expanded module-by-module.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260911_odoo_module_catalog"
down_revision = "20260831legal"
branch_labels = None
depends_on = None


MODULES = [
    # Core / platform
    ("dashboard", "Dashboard", "لوحة التحكم", "Productivity", True, 5),
    ("users", "Users & Access", "المستخدمون والصلاحيات", "Settings", True, 10),
    ("companies", "Companies", "الشركات", "Settings", True, 15),
    ("branches", "Branches", "الفروع", "Settings", True, 20),
    ("contacts", "Contacts", "جهات الاتصال", "Essentials", True, 25),
    ("calendar", "Calendar", "التقويم", "Productivity", False, 30),
    ("discuss", "Discuss", "المناقشات", "Productivity", False, 35),

    # Finance
    ("accounting", "Accounting", "المحاسبة", "Finance", True, 100),
    ("invoicing", "Invoicing", "الفوترة", "Finance", False, 105),
    ("expenses", "Expenses", "المصروفات", "Finance", False, 110),
    ("payments", "Payments", "المدفوعات", "Finance", False, 115),
    ("bank_reconciliation", "Bank Reconciliation", "التسويات البنكية", "Finance", False, 120),
    ("assets", "Fixed Assets", "الأصول الثابتة", "Finance", False, 125),
    ("budgets", "Budgets", "الموازنات", "Finance", False, 130),
    ("analytic_accounting", "Analytic Accounting", "المحاسبة التحليلية", "Finance", False, 135),
    ("taxes", "Taxes", "الضرائب", "Finance", True, 140),
    ("egyptian_einvoice", "Egyptian e-Invoice", "الفاتورة الإلكترونية المصرية", "Finance", False, 145),

    # Sales / CRM
    ("crm", "CRM", "إدارة علاقات العملاء", "Sales", False, 200),
    ("sales", "Sales", "المبيعات", "Sales", True, 205),
    ("subscriptions", "Subscriptions", "الاشتراكات", "Sales", False, 210),
    ("rental", "Rental", "التأجير", "Sales", False, 215),
    ("commissions", "Sales Commissions", "عمولات المبيعات", "Sales", False, 220),
    ("pos", "Point of Sale", "نقطة البيع", "Sales", False, 225),

    # Supply chain
    ("purchasing", "Purchase", "المشتريات", "Supply Chain", True, 300),
    ("inventory", "Inventory", "المخزون", "Supply Chain", True, 305),
    ("barcode", "Barcode", "الباركود", "Supply Chain", False, 310),
    ("shipping", "Shipping & Delivery", "الشحن والتوصيل", "Supply Chain", False, 315),
    ("quality", "Quality", "الجودة", "Supply Chain", False, 320),
    ("maintenance", "Maintenance", "الصيانة", "Supply Chain", False, 325),
    ("manufacturing", "Manufacturing", "التصنيع", "Supply Chain", False, 330),
    ("plm", "Product Lifecycle", "دورة حياة المنتج", "Supply Chain", False, 335),
    ("repairs", "Repairs", "الإصلاحات", "Supply Chain", False, 340),
    ("uom", "Units of Measure", "وحدات القياس", "Supply Chain", True, 345),

    # Services
    ("projects", "Project", "المشروعات", "Services", False, 400),
    ("timesheets", "Timesheets", "ساعات العمل", "Services", False, 405),
    ("planning", "Planning", "التخطيط", "Services", False, 410),
    ("field_service", "Field Service", "الخدمة الميدانية", "Services", False, 415),
    ("helpdesk", "Helpdesk", "خدمة العملاء", "Services", False, 420),

    # HR
    ("hr", "Employees", "الموظفون", "Human Resources", True, 500),
    ("attendance", "Attendances", "الحضور والانصراف", "Human Resources", False, 505),
    ("leave", "Time Off", "الإجازات", "Human Resources", False, 510),
    ("payroll", "Payroll", "الرواتب", "Human Resources", False, 515),
    ("recruitment", "Recruitment", "التوظيف", "Human Resources", False, 520),
    ("appraisals", "Appraisals", "تقييم الأداء", "Human Resources", False, 525),
    ("fleet", "Fleet", "إدارة الأسطول", "Human Resources", False, 530),

    # Website / commerce
    ("website", "Website", "الموقع الإلكتروني", "Websites", False, 600),
    ("ecommerce", "eCommerce", "التجارة الإلكترونية", "Websites", False, 605),
    ("integrations", "Integrations", "التكاملات", "Settings", False, 610),
    ("salla", "Salla Connector", "تكامل سلة", "Integrations", False, 615),

    # Marketing / productivity
    ("email_marketing", "Email Marketing", "التسويق بالبريد الإلكتروني", "Marketing", False, 700),
    ("sms_marketing", "SMS Marketing", "التسويق عبر الرسائل", "Marketing", False, 705),
    ("marketing_automation", "Marketing Automation", "أتمتة التسويق", "Marketing", False, 710),
    ("events", "Events", "الفعاليات", "Marketing", False, 715),
    ("surveys", "Surveys", "الاستبيانات", "Marketing", False, 720),
    ("documents", "Documents", "المستندات", "Productivity", False, 725),
    ("sign", "Sign", "التوقيع الإلكتروني", "Productivity", False, 730),
    ("approvals", "Approvals", "الموافقات", "Productivity", False, 735),
    ("reports", "Reporting & BI", "التقارير والتحليلات", "Productivity", True, 740),
    ("ai", "AI Assistant", "مساعد الذكاء الاصطناعي", "Productivity", False, 745),
]


CORE_CODES = {
    "dashboard",
    "users",
    "companies",
    "branches",
    "contacts",
    "accounting",
    "taxes",
    "sales",
    "purchasing",
    "inventory",
    "uom",
    "reports",
}


def upgrade() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    system_modules = sa.Table("system_modules", metadata, autoload_with=bind)
    plan_modules = sa.Table("plan_modules", metadata, autoload_with=bind)
    subscription_plans = sa.Table("subscription_plans", metadata, autoload_with=bind)

    for code, name_en, name_ar, category, application, sequence in MODULES:
        existing = bind.execute(
            sa.select(system_modules.c.id).where(system_modules.c.code == code)
        ).scalar_one_or_none()
        values = {
            "code": code,
            "name_ar": name_ar,
            "name_en": name_en,
            "description_ar": f"وحدة {name_ar} ضمن منصة PrimeERP.",
            "description_en": f"PrimeERP application module: {name_en} ({category}).",
            "is_core": code in CORE_CODES,
            "is_active": True,
            "display_order": sequence,
        }
        if existing is None:
            bind.execute(system_modules.insert().values(**values))
        else:
            bind.execute(
                system_modules.update()
                .where(system_modules.c.id == existing)
                .values(**values)
            )

    # Every active subscription plan receives the core application set.  Optional
    # applications remain available in the catalog and can be priced/enabled per plan.
    core_ids = bind.execute(
        sa.select(system_modules.c.id).where(
            system_modules.c.code.in_(sorted(CORE_CODES)),
            system_modules.c.is_active.is_(True),
        )
    ).scalars().all()
    plan_ids = bind.execute(
        sa.select(subscription_plans.c.id).where(subscription_plans.c.is_active.is_(True))
    ).scalars().all()

    for plan_id in plan_ids:
        for module_id in core_ids:
            exists = bind.execute(
                sa.select(plan_modules.c.id).where(
                    plan_modules.c.plan_id == plan_id,
                    plan_modules.c.module_id == module_id,
                )
            ).scalar_one_or_none()
            if exists is None:
                bind.execute(
                    plan_modules.insert().values(
                        plan_id=plan_id,
                        module_id=module_id,
                        is_enabled=True,
                    )
                )


def downgrade() -> None:
    # Keep module rows because plans/tenants may already reference them.  This is
    # intentionally a non-destructive catalog migration.
    pass
