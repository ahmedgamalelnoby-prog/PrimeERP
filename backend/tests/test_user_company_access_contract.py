from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_company_access_table_has_one_default_per_user():
    source = read("app/modules/companies/models.py")
    assert 'Table(\n    "user_company_access"' in source
    assert '"uq_user_company_access_one_default"' in source
    assert "postgresql_where=user_company_access.c.is_default.is_(True)" in source


def test_company_list_is_limited_to_assigned_companies():
    source = read("app/modules/companies/router.py")
    assert "user_company_access.c.user_id == current_user.id" in source


def test_company_settings_reject_unassigned_company():
    source = read("app/modules/company_settings/router.py")
    assert "has_company_access(db, user.id, company.id, tenant_id)" in source


def test_selected_company_header_is_validated_for_authenticated_user():
    source = read("app/modules/identity/dependencies/current_user.py")
    assert 'alias="X-Company-ID"' in source
    assert "has_company_access(db, user.id, company_id, user.tenant_id)" in source


def test_user_company_assignment_endpoint_validates_tenant_and_default():
    source = read("app/modules/identity/api/users.py")
    assert 'prefix="/users"' in source
    assert '"/{user_id}/companies"' in source
    assert '"/{user_id}/companies/available"' in source
    assert "default_company_id not in self.company_ids" in source
    assert "Company.tenant_id == tenant_id" in source


def test_migration_backfills_existing_tenant_company_access():
    source = read("alembic/versions/20261107_user_company_access.py")
    assert "ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY c.id)" in source
    assert "ranked.position = 1" in source


def test_accounting_treasury_pos_and_hr_enforce_assigned_company_access():
    modules = {
        "accounting/router.py": "def _company_for_user",
        "treasury/router.py": "def _company",
        "pos/router.py": "def _company",
        "hr/router.py": "def _company_for_user",
        "commerce/router.py": "def _company_for_user",
        "reports/router.py": "def _company_for_user",
        "shipping/router.py": "def _company_for_user",
        "inventory/transfers/router.py": "def _company_for_user",
        "inventory/stock_moves/router.py": "def _company_for_user",
        "enterprise/router.py": "def company_for_user",
        "catalog/router.py": "def _company_for_user",
        "taxes/router.py": "def _company_for_user",
        "egyptian_einvoice/router.py": "def _company_for_user",
        "mobile/router.py": "def company_ok",
        "manufacturing/bom/router.py": "def _company",
        "crm/api.py": "def _company",
        "uom/router.py": "def _company_for_user",
        "operations/approvals/router.py": "def _company",
        "inventory/items/router.py": "def _company_for_user",
        "inventory/warehouses/router.py": "def _company_for_user",
        "inventory/adjustments/router.py": "def _company_for_user",
        "inventory/costing/router.py": "def _company_for_user",
        "inventory/locations/router.py": "def _company_for_user",
        "inventory/reservations/router.py": "def _company_for_user",
        "commissions/router.py": "def company_for_user",
        "integrations/router.py": "def _company_for_user",
        "notifications/router.py": "def _company",
        "platform/developer/router.py": "def company_ok",
        "helpdesk_ai/router.py": "def _company_for_user",
        "catalog/bundle_router.py": "def guard_company",
        "catalog/pricing_engine_router.py": "def _company_for_user",
        "catalog/variant_router.py": "def _company_for_user",
        "enterprise/finance_router.py": "def company_ok",
        "shipping/reports_router.py": "def _company",
        "shipping/settlement_router.py": "def _company_for_user",
        "shipping/status_router.py": "def _company",
    }
    for module, helper in modules.items():
        source = read(f"app/modules/{module}")
        assert "from app.modules.companies.access import has_company_access" in source
        assert helper in source
        assert (
            "has_company_access(db, user.id, company.id, company.tenant_id)" in source
            or "has_company_access(db,user.id,company.id,company.tenant_id)" in source
        )
        assert "not user.is_platform_admin" in source


    jurisdiction = read("app/modules/jurisdiction/router.py")
    assert "has_company_access(db, user.id, obj.id, obj.tenant_id)" in jurisdiction
    assert "has_company_access(db, user.id, obj.company_id, get_effective_tenant_id(user))" in jurisdiction

    bank_reconciliation = read("app/modules/treasury/bank_reconciliation/service.py")
    assert "has_company_access(db, user.id, company.id, company.tenant_id)" in bank_reconciliation

    transactions = read("app/modules/transactions/services/transaction_service.py")
    assert "has_company_access(db, current_user.id, company_id, tenant_id)" in transactions
    assert "allowed_company_ids = None if current_user.is_platform_admin else assigned_company_ids(db, current_user.id, tenant_id)" in transactions
    assert "transaction.company_id, transaction.tenant_id" in transactions


def test_hr_company_scoped_endpoints_use_authenticated_user_assignment():
    source = read("app/modules/hr/router.py")
    assert "_company_for_tenant" not in source
    assert source.count("_company_for_user(db, company_id, current_user)") == 17




def test_extended_company_scopes_are_enforced():
    chart_of_accounts = read("app/modules/accounting/chart_of_accounts/router.py")
    assert "has_company_access(db, current_user.id, company_id, tenant_id)" in chart_of_accounts
    assert "not current_user.is_platform_admin" in chart_of_accounts
    fiscal_years = read("app/modules/accounting/fiscal_years/services/fiscal_year_service.py")
    assert "has_company_access(db, current_user.id, company_id, tenant_id)" in fiscal_years
    assert "current_user=current_user" in fiscal_years
    accounting_reports = read("app/modules/accounting/reports/router.py")
    assert "has_company_access(db, current_user.id, company_id, tenant_id(current_user))" in accounting_reports
    audit = read("app/modules/audit/router.py")
    assert "allowed_company_ids = assigned_company_ids(db, current_user.id, current_user.tenant_id)" in audit
    shipping_pricing = read("app/modules/shipping/pricing_router.py")
    assert "has_company_access(db, user.id, obj.id, obj.tenant_id)" in shipping_pricing
    shipping_accounting = read("app/modules/shipping/accounting_router.py")
    assert "has_company_access(db, current_user.id, company.id, company.tenant_id)" in shipping_accounting
    product_mapping = read("app/modules/integrations/product_mapping_router.py")
    assert "has_company_access(db, user.id, row.company_id, row.tenant_id)" in product_mapping


def test_number_sequences_are_limited_to_assigned_companies():
    router = read("app/modules/transactions/api/router.py")
    repository = read("app/modules/transactions/repositories/number_sequence_repository.py")
    assert "require_assigned_company(db, payload.company_id, current_user)" in router
    assert "allowed_ids = None if current_user.is_platform_admin else assigned_company_ids(db, current_user.id, tenant_id)" in router
    assert "company_ids=allowed_ids if company_id is None else None" in router
    assert "NumberSequence.company_id.in_(company_ids)" in repository
