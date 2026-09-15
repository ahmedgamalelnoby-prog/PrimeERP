"""Harden fiscal/period lifecycle flags at database level.

Revision ID: 20260916_fiscal_lifecycle_guards
Revises: 20260916_fiscal_period_scope_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260916_fiscal_lifecycle_guards"
down_revision = "20260916_fiscal_period_scope_integrity"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    if conn.execute(
        sa.text(
            """
            SELECT 1
            FROM accounting_periods
            WHERE allow_posting
              AND status NOT IN ('open', 'closing')
            LIMIT 1
            """
        )
    ).scalar() is not None:
        raise RuntimeError(
            "Cannot apply fiscal lifecycle guards: accounting period allow_posting/status data is inconsistent"
        )

    if conn.execute(
        sa.text(
            """
            SELECT 1
            FROM fiscal_years a
            JOIN fiscal_years b
              ON a.tenant_id = b.tenant_id
             AND a.company_id = b.company_id
             AND a.id < b.id
            WHERE a.is_current AND b.is_current
            LIMIT 1
            """
        )
    ).scalar() is not None:
        raise RuntimeError(
            "Cannot apply fiscal lifecycle guards: more than one current fiscal year exists for a company"
        )

    op.create_index(
        "ux_fiscal_year_current_scope",
        "fiscal_years",
        ["tenant_id", "company_id"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )

    op.create_check_constraint(
        "ck_accounting_period_allow_posting_state",
        "accounting_periods",
        "NOT allow_posting OR status IN ('open', 'closing')",
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION validate_accounting_period_lifecycle()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        DECLARE
            fy_status TEXT;
            has_journal_entries BOOLEAN;
        BEGIN
            SELECT status
              INTO fy_status
              FROM fiscal_years
             WHERE tenant_id = NEW.tenant_id
               AND company_id = NEW.company_id
               AND id = NEW.fiscal_year_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'Accounting period fiscal year is outside tenant/company scope';
            END IF;

            IF NEW.allow_posting
               AND NEW.status NOT IN ('open', 'closing')
            THEN
                RAISE EXCEPTION 'Accounting period allow_posting requires open or closing status';
            END IF;

            IF NEW.status IN ('open', 'closing')
               AND fy_status NOT IN ('open', 'closing')
            THEN
                RAISE EXCEPTION 'Accounting period cannot be open while fiscal year is not open';
            END IF;

            IF TG_OP = 'UPDATE'
               AND (
                    NEW.tenant_id <> OLD.tenant_id
                 OR NEW.company_id <> OLD.company_id
                 OR NEW.fiscal_year_id <> OLD.fiscal_year_id
                 OR NEW.start_date <> OLD.start_date
                 OR NEW.end_date <> OLD.end_date
               )
            THEN
                SELECT EXISTS(
                    SELECT 1
                    FROM journal_entries je
                    WHERE je.tenant_id = OLD.tenant_id
                      AND je.company_id = OLD.company_id
                      AND je.period_id = OLD.id
                ) INTO has_journal_entries;

                IF has_journal_entries THEN
                    RAISE EXCEPTION 'Accounting period scope/dates cannot change after journal entries exist';
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_validate_accounting_period_lifecycle
        ON accounting_periods;
        CREATE TRIGGER trg_validate_accounting_period_lifecycle
        BEFORE INSERT OR UPDATE OF tenant_id, company_id, fiscal_year_id, start_date, end_date, status, allow_posting
        ON accounting_periods
        FOR EACH ROW
        EXECUTE FUNCTION validate_accounting_period_lifecycle();
        """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS trg_validate_accounting_period_lifecycle ON accounting_periods"
    )
    op.execute("DROP FUNCTION IF EXISTS validate_accounting_period_lifecycle()")
    op.drop_constraint(
        "ck_accounting_period_allow_posting_state",
        "accounting_periods",
        type_="check",
    )
    op.drop_index("ux_fiscal_year_current_scope", table_name="fiscal_years")
