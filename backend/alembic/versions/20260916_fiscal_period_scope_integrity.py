"""Harden fiscal year / accounting period scope and journal date integrity.

Revision ID: 20260916_fiscal_period_scope_integrity
Revises: 20260915_journal_company_tenant_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260916_fiscal_period_scope_integrity"
down_revision = "20260915_journal_company_tenant_integrity"
branch_labels = None
depends_on = None


def _scalar(conn, sql, params=None):
    return conn.execute(sa.text(sql), params or {}).scalar()


def upgrade():
    conn = op.get_bind()

    # Fail before installing constraints if legacy rows already violate the
    # intended tenant/company/fiscal-period ownership model.
    checks = [
        (
            "fiscal_year_company_tenant_mismatch",
            """
            SELECT 1
            FROM fiscal_years fy
            JOIN companies c ON c.id = fy.company_id
            WHERE fy.tenant_id <> c.tenant_id
            LIMIT 1
            """,
        ),
        (
            "accounting_period_company_tenant_mismatch",
            """
            SELECT 1
            FROM accounting_periods ap
            JOIN companies c ON c.id = ap.company_id
            WHERE ap.tenant_id <> c.tenant_id
            LIMIT 1
            """,
        ),
        (
            "accounting_period_fiscal_year_scope_mismatch",
            """
            SELECT 1
            FROM accounting_periods ap
            JOIN fiscal_years fy ON fy.id = ap.fiscal_year_id
            WHERE ap.tenant_id <> fy.tenant_id
               OR ap.company_id <> fy.company_id
            LIMIT 1
            """,
        ),
        (
            "accounting_period_outside_fiscal_year",
            """
            SELECT 1
            FROM accounting_periods ap
            JOIN fiscal_years fy ON fy.id = ap.fiscal_year_id
            WHERE ap.start_date < fy.start_date
               OR ap.end_date > fy.end_date
            LIMIT 1
            """,
        ),
        (
            "fiscal_year_overlap",
            """
            SELECT 1
            FROM fiscal_years a
            JOIN fiscal_years b
              ON a.tenant_id = b.tenant_id
             AND a.company_id = b.company_id
             AND a.id < b.id
             AND a.start_date <= b.end_date
             AND b.start_date <= a.end_date
            LIMIT 1
            """,
        ),
        (
            "accounting_period_overlap",
            """
            SELECT 1
            FROM accounting_periods a
            JOIN accounting_periods b
              ON a.tenant_id = b.tenant_id
             AND a.company_id = b.company_id
             AND a.id < b.id
             AND a.start_date <= b.end_date
             AND b.start_date <= a.end_date
            WHERE NOT (a.is_adjustment OR b.is_adjustment)
            LIMIT 1
            """,
        ),
        (
            "journal_entry_fiscal_year_scope_mismatch",
            """
            SELECT 1
            FROM journal_entries je
            JOIN fiscal_years fy ON fy.id = je.fiscal_year_id
            WHERE je.tenant_id <> fy.tenant_id
               OR je.company_id <> fy.company_id
            LIMIT 1
            """,
        ),
        (
            "journal_entry_period_scope_mismatch",
            """
            SELECT 1
            FROM journal_entries je
            JOIN accounting_periods ap ON ap.id = je.period_id
            WHERE je.tenant_id <> ap.tenant_id
               OR je.company_id <> ap.company_id
            LIMIT 1
            """,
        ),
        (
            "journal_entry_period_fiscal_year_mismatch",
            """
            SELECT 1
            FROM journal_entries je
            JOIN accounting_periods ap ON ap.id = je.period_id
            WHERE ap.fiscal_year_id <> je.fiscal_year_id
            LIMIT 1
            """,
        ),
        (
            "journal_entry_date_outside_period",
            """
            SELECT 1
            FROM journal_entries je
            JOIN accounting_periods ap ON ap.id = je.period_id
            WHERE je.entry_date < ap.start_date
               OR je.entry_date > ap.end_date
            LIMIT 1
            """,
        ),
        (
            "journal_entry_date_outside_fiscal_year",
            """
            SELECT 1
            FROM journal_entries je
            JOIN fiscal_years fy ON fy.id = je.fiscal_year_id
            WHERE je.entry_date < fy.start_date
               OR je.entry_date > fy.end_date
            LIMIT 1
            """,
        ),
    ]

    for name, sql in checks:
        if _scalar(conn, sql) is not None:
            raise RuntimeError(
                f"Cannot apply {revision}: pre-flight check failed: {name}"
            )

    # Composite FK targets. Existing single-column FKs remain in place for
    # compatibility; these additional constraints enforce same-tenant/company
    # ownership at the database boundary.
    op.create_unique_constraint(
        "uq_fiscal_year_tenant_company_id",
        "fiscal_years",
        ["tenant_id", "company_id", "id"],
    )
    op.create_unique_constraint(
        "uq_accounting_period_tenant_company_id",
        "accounting_periods",
        ["tenant_id", "company_id", "id"],
    )
    op.create_unique_constraint(
        "uq_accounting_period_scope_fy_id",
        "accounting_periods",
        ["tenant_id", "company_id", "fiscal_year_id", "id"],
    )

    op.create_foreign_key(
        "fk_fiscal_year_company_tenant",
        "fiscal_years",
        "companies",
        ["tenant_id", "company_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_accounting_period_company_tenant",
        "accounting_periods",
        "companies",
        ["tenant_id", "company_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_accounting_period_fiscal_year_scope",
        "accounting_periods",
        "fiscal_years",
        ["tenant_id", "company_id", "fiscal_year_id"],
        ["tenant_id", "company_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_journal_entry_fiscal_year_scope",
        "journal_entries",
        "fiscal_years",
        ["tenant_id", "company_id", "fiscal_year_id"],
        ["tenant_id", "company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_journal_entry_period_scope",
        "journal_entries",
        "accounting_periods",
        ["tenant_id", "company_id", "period_id"],
        ["tenant_id", "company_id", "id"],
        ondelete="RESTRICT",
    )

    # Periods are a legal/accounting boundary, not just descriptive dates.
    # Adjustment periods are intentionally excluded from the normal overlap
    # rule so a controlled adjustment period can coexist with a normal month.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE fiscal_years
        ADD CONSTRAINT ex_fiscal_year_scope_no_overlap
        EXCLUDE USING gist (
            tenant_id WITH =,
            company_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&
        )
        """
    )
    op.execute(
        """
        ALTER TABLE accounting_periods
        ADD CONSTRAINT ex_accounting_period_scope_no_overlap
        EXCLUDE USING gist (
            tenant_id WITH =,
            company_id WITH =,
            daterange(start_date, end_date, '[]') WITH &&
        )
        WHERE (NOT is_adjustment)
        """
    )

    # Cross-table date/status rules cannot be represented by CHECK constraints.
    # A trigger makes the invariant hold for every writer, including direct SQL.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION validate_journal_entry_period_scope()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            p_start DATE;
            p_end DATE;
            p_fy_id INTEGER;
            p_status TEXT;
            p_allow_posting BOOLEAN;
            fy_start DATE;
            fy_end DATE;
        BEGIN
            SELECT start_date, end_date, fiscal_year_id, status, allow_posting
              INTO p_start, p_end, p_fy_id, p_status, p_allow_posting
              FROM accounting_periods
             WHERE tenant_id = NEW.tenant_id
               AND company_id = NEW.company_id
               AND id = NEW.period_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Journal entry period is outside tenant/company scope';
            END IF;

            IF p_fy_id <> NEW.fiscal_year_id THEN
                RAISE EXCEPTION 'Journal entry fiscal year does not match accounting period';
            END IF;

            IF NEW.entry_date < p_start OR NEW.entry_date > p_end THEN
                RAISE EXCEPTION 'Journal entry date is outside accounting period';
            END IF;

            SELECT start_date, end_date
              INTO fy_start, fy_end
              FROM fiscal_years
             WHERE tenant_id = NEW.tenant_id
               AND company_id = NEW.company_id
               AND id = NEW.fiscal_year_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Journal entry fiscal year is outside tenant/company scope';
            END IF;

            IF NEW.entry_date < fy_start OR NEW.entry_date > fy_end THEN
                RAISE EXCEPTION 'Journal entry date is outside fiscal year';
            END IF;

            IF NEW.status IN ('approved', 'posted')
               AND (p_status NOT IN ('open', 'closing') OR NOT p_allow_posting)
            THEN
                RAISE EXCEPTION 'Journal entry cannot be approved/posted into a non-posting accounting period';
            END IF;

            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_validate_journal_entry_period_scope
        ON journal_entries;
        CREATE TRIGGER trg_validate_journal_entry_period_scope
        BEFORE INSERT OR UPDATE OF tenant_id, company_id, fiscal_year_id, period_id, entry_date, status
        ON journal_entries
        FOR EACH ROW
        EXECUTE FUNCTION validate_journal_entry_period_scope();
        """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS trg_validate_journal_entry_period_scope ON journal_entries"
    )
    op.execute("DROP FUNCTION IF EXISTS validate_journal_entry_period_scope()")
    op.drop_constraint(
        "ex_accounting_period_scope_no_overlap",
        "accounting_periods",
        type_="exclude",
    )
    op.drop_constraint(
        "ex_fiscal_year_scope_no_overlap",
        "fiscal_years",
        type_="exclude",
    )
    op.drop_constraint("fk_journal_entry_period_scope", "journal_entries", type_="foreignkey")
    op.drop_constraint("fk_journal_entry_fiscal_year_scope", "journal_entries", type_="foreignkey")
    op.drop_constraint("fk_accounting_period_fiscal_year_scope", "accounting_periods", type_="foreignkey")
    op.drop_constraint("fk_accounting_period_company_tenant", "accounting_periods", type_="foreignkey")
    op.drop_constraint("fk_fiscal_year_company_tenant", "fiscal_years", type_="foreignkey")
    op.drop_constraint("uq_accounting_period_scope_fy_id", "accounting_periods", type_="unique")
    op.drop_constraint("uq_accounting_period_tenant_company_id", "accounting_periods", type_="unique")
    op.drop_constraint("uq_fiscal_year_tenant_company_id", "fiscal_years", type_="unique")
