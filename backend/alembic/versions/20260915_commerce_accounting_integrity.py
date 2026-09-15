"""Harden commerce accounting settings company integrity.

Revision ID: 20260915_commerce_accounting_integrity
Revises: 20260915_inventory_integrity_hardening
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_commerce_accounting_integrity"
down_revision = "20260915_inventory_integrity_hardening"
branch_labels = None
depends_on = None


def _preflight(conn):
    checks = [
        ("commerce_accounting_settings.sales_journal_id", """
            SELECT 1 FROM commerce_accounting_settings s
            JOIN accounting_journals j ON j.id = s.sales_journal_id
            WHERE j.company_id <> s.company_id LIMIT 1
        """),
        ("commerce_accounting_settings.purchase_journal_id", """
            SELECT 1 FROM commerce_accounting_settings s
            JOIN accounting_journals j ON j.id = s.purchase_journal_id
            WHERE j.company_id <> s.company_id LIMIT 1
        """),
        ("commerce_accounting_settings.cash_journal_id", """
            SELECT 1 FROM commerce_accounting_settings s
            JOIN accounting_journals j ON j.id = s.cash_journal_id
            WHERE j.company_id <> s.company_id LIMIT 1
        """),
        ("commerce_accounting_settings account combinations", """
            SELECT 1 FROM commerce_accounting_settings s
            JOIN account_combinations a ON a.id IN (
                s.ar_account_id, s.ap_account_id, s.sales_account_id,
                s.purchase_account_id, s.inventory_account_id, s.cogs_account_id,
                s.output_vat_account_id, s.input_vat_account_id,
                COALESCE(s.wht_account_id, -1), s.default_payment_account_id
            )
            WHERE a.company_id <> s.company_id LIMIT 1
        """),
        ("commerce_accounting_settings.default_branch_id", """
            SELECT 1 FROM commerce_accounting_settings s
            JOIN branches b ON b.id = s.default_branch_id
            WHERE b.company_id <> s.company_id LIMIT 1
        """),
    ]
    for label, sql in checks:
        if conn.execute(sa.text(sql)).first() is not None:
            raise RuntimeError(f"Preflight failed: {label} contains cross-company references")


def upgrade():
    conn = op.get_bind()
    _preflight(conn)

    op.create_unique_constraint(
        "uq_accounting_journals_company_id",
        "accounting_journals",
        ["company_id", "id"],
    )
    op.create_unique_constraint(
        "uq_account_combinations_company_id",
        "account_combinations",
        ["company_id", "id"],
    )
    op.create_unique_constraint(
        "uq_branches_company_id",
        "branches",
        ["company_id", "id"],
    )

    op.create_foreign_key(
        "fk_commerce_settings_sales_journal_company",
        "commerce_accounting_settings",
        "accounting_journals",
        ["company_id", "sales_journal_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_commerce_settings_purchase_journal_company",
        "commerce_accounting_settings",
        "accounting_journals",
        ["company_id", "purchase_journal_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_commerce_settings_cash_journal_company",
        "commerce_accounting_settings",
        "accounting_journals",
        ["company_id", "cash_journal_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )

    account_columns = (
        "ar_account_id", "ap_account_id", "sales_account_id", "purchase_account_id",
        "inventory_account_id", "cogs_account_id", "output_vat_account_id",
        "input_vat_account_id", "default_payment_account_id",
    )
    for column in account_columns:
        op.create_foreign_key(
            f"fk_commerce_settings_{column}_company",
            "commerce_accounting_settings",
            "account_combinations",
            ["company_id", column],
            ["company_id", "id"],
            ondelete="RESTRICT",
        )
    op.create_foreign_key(
        "fk_commerce_settings_wht_account_company",
        "commerce_accounting_settings",
        "account_combinations",
        ["company_id", "wht_account_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_commerce_settings_default_branch_company",
        "commerce_accounting_settings",
        "branches",
        ["company_id", "default_branch_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )


def downgrade():
    op.drop_constraint("fk_commerce_settings_default_branch_company", "commerce_accounting_settings", type_="foreignkey")
    op.drop_constraint("fk_commerce_settings_wht_account_company", "commerce_accounting_settings", type_="foreignkey")
    for column in (
        "ar_account_id", "ap_account_id", "sales_account_id", "purchase_account_id",
        "inventory_account_id", "cogs_account_id", "output_vat_account_id",
        "input_vat_account_id", "default_payment_account_id",
    ):
        op.drop_constraint(f"fk_commerce_settings_{column}_company", "commerce_accounting_settings", type_="foreignkey")
    op.drop_constraint("fk_commerce_settings_cash_journal_company", "commerce_accounting_settings", type_="foreignkey")
    op.drop_constraint("fk_commerce_settings_purchase_journal_company", "commerce_accounting_settings", type_="foreignkey")
    op.drop_constraint("fk_commerce_settings_sales_journal_company", "commerce_accounting_settings", type_="foreignkey")
    op.drop_constraint("uq_branches_company_id", "branches", type_="unique")
    op.drop_constraint("uq_account_combinations_company_id", "account_combinations", type_="unique")
    op.drop_constraint("uq_accounting_journals_company_id", "accounting_journals", type_="unique")
