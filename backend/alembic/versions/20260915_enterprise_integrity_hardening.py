"""Harden tenant/company and legal-data integrity at database level.

Revision ID: 20260915_enterprise_integrity_hardening
Revises: 20260915_merge_all_heads
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_enterprise_integrity_hardening"
down_revision = "20260915_merge_all_heads"
branch_labels = None
depends_on = None


def _assert_clean(conn, sql: str, message: str) -> None:
    if conn.execute(sa.text(sql)).scalar():
        raise RuntimeError(message)


def upgrade():
    conn = op.get_bind()

    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM accounting_cost_centers cc JOIN accounting_departments d ON d.id = cc.department_id WHERE cc.company_id <> d.company_id)", "Cannot harden accounting_cost_centers: cross-company department references exist.")
    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM accounting_cost_centers cc JOIN branches b ON b.id = cc.branch_id WHERE cc.branch_id IS NOT NULL AND cc.company_id <> b.company_id)", "Cannot harden accounting_cost_centers: cross-company branch references exist.")
    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM natural_accounts child JOIN natural_accounts parent ON parent.id = child.parent_id WHERE child.parent_id IS NOT NULL AND child.company_id <> parent.company_id)", "Cannot harden natural_accounts: cross-company parent references exist.")
    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM account_combinations ac JOIN accounting_departments d ON d.id = ac.department_id JOIN accounting_cost_centers cc ON cc.id = ac.cost_center_id JOIN natural_accounts na ON na.id = ac.natural_account_id WHERE ac.company_id <> d.company_id OR ac.company_id <> cc.company_id OR ac.company_id <> na.company_id)", "Cannot harden account_combinations: cross-company dimension references exist.")
    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM company_jurisdictions WHERE effective_to IS NOT NULL AND effective_to < effective_from)", "Cannot harden company_jurisdictions: invalid effective date ranges exist.")
    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM partner_jurisdictions WHERE effective_to IS NOT NULL AND effective_to < effective_from)", "Cannot harden partner_jurisdictions: invalid effective date ranges exist.")
    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM jurisdiction_tax_rules WHERE effective_to IS NOT NULL AND effective_to < effective_from)", "Cannot harden jurisdiction_tax_rules: invalid effective date ranges exist.")
    _assert_clean(conn, "SELECT EXISTS (SELECT 1 FROM jurisdiction_decisions d JOIN commerce_partners p ON p.id = d.partner_id WHERE d.partner_id IS NOT NULL AND d.company_id <> p.company_id)", "Cannot harden jurisdiction_decisions: cross-company partner references exist.")

    # PostgreSQL requires an exact UNIQUE/PK target for composite foreign keys.
    op.create_unique_constraint("uq_accounting_departments_company_id", "accounting_departments", ["company_id", "id"])
    op.create_unique_constraint("uq_accounting_cost_centers_company_id", "accounting_cost_centers", ["company_id", "id"])
    op.create_unique_constraint("uq_natural_accounts_company_id", "natural_accounts", ["company_id", "id"])
    op.create_unique_constraint("uq_branches_company_id", "branches", ["company_id", "id"])
    op.create_unique_constraint("uq_commerce_partners_company_id", "commerce_partners", ["company_id", "id"])
    op.create_unique_constraint("uq_jurisdiction_decisions_company_id", "jurisdiction_decisions", ["company_id", "id"])

    op.create_foreign_key("fk_cost_center_department_same_company", "accounting_cost_centers", "accounting_departments", ["company_id", "department_id"], ["company_id", "id"], ondelete="CASCADE")
    op.create_foreign_key("fk_cost_center_branch_same_company", "accounting_cost_centers", "branches", ["company_id", "branch_id"], ["company_id", "id"], ondelete="SET NULL")
    op.create_foreign_key("fk_natural_account_parent_same_company", "natural_accounts", "natural_accounts", ["company_id", "parent_id"], ["company_id", "id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_account_combination_department_same_company", "account_combinations", "accounting_departments", ["company_id", "department_id"], ["company_id", "id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_account_combination_cost_center_same_company", "account_combinations", "accounting_cost_centers", ["company_id", "cost_center_id"], ["company_id", "id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_account_combination_natural_account_same_company", "account_combinations", "natural_accounts", ["company_id", "natural_account_id"], ["company_id", "id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_jurisdiction_decision_partner_same_company", "jurisdiction_decisions", "commerce_partners", ["company_id", "partner_id"], ["company_id", "id"], ondelete="SET NULL")

    op.create_check_constraint("ck_company_jurisdiction_effective_range", "company_jurisdictions", "effective_to IS NULL OR effective_to >= effective_from")
    op.create_check_constraint("ck_partner_jurisdiction_effective_range", "partner_jurisdictions", "effective_to IS NULL OR effective_to >= effective_from")
    op.create_check_constraint("ck_tax_rule_effective_range", "jurisdiction_tax_rules", "effective_to IS NULL OR effective_to >= effective_from")
    op.create_unique_constraint("uq_tax_rate_company_code", "tax_rates", ["company_id", "code"])


def downgrade():
    op.drop_constraint("uq_tax_rate_company_code", "tax_rates", type_="unique")
    op.drop_constraint("ck_tax_rule_effective_range", "jurisdiction_tax_rules", type_="check")
    op.drop_constraint("ck_partner_jurisdiction_effective_range", "partner_jurisdictions", type_="check")
    op.drop_constraint("ck_company_jurisdiction_effective_range", "company_jurisdictions", type_="check")
    op.drop_constraint("fk_jurisdiction_decision_partner_same_company", "jurisdiction_decisions", type_="foreignkey")
    op.drop_constraint("fk_account_combination_natural_account_same_company", "account_combinations", type_="foreignkey")
    op.drop_constraint("fk_account_combination_cost_center_same_company", "account_combinations", type_="foreignkey")
    op.drop_constraint("fk_account_combination_department_same_company", "account_combinations", type_="foreignkey")
    op.drop_constraint("fk_natural_account_parent_same_company", "natural_accounts", type_="foreignkey")
    op.drop_constraint("fk_cost_center_branch_same_company", "accounting_cost_centers", type_="foreignkey")
    op.drop_constraint("fk_cost_center_department_same_company", "accounting_cost_centers", type_="foreignkey")
    op.drop_constraint("uq_jurisdiction_decisions_company_id", "jurisdiction_decisions", type_="unique")
    op.drop_constraint("uq_commerce_partners_company_id", "commerce_partners", type_="unique")
    op.drop_constraint("uq_branches_company_id", "branches", type_="unique")
    op.drop_constraint("uq_natural_accounts_company_id", "natural_accounts", type_="unique")
    op.drop_constraint("uq_accounting_cost_centers_company_id", "accounting_cost_centers", type_="unique")
    op.drop_constraint("uq_accounting_departments_company_id", "accounting_departments", type_="unique")
