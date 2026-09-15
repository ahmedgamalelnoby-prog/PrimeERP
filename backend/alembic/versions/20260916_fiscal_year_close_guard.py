"""Prevent fiscal-year closure while unposted journal entries remain.

Revision ID: 20260916_fiscal_year_close_guard
Revises: 20260916_tax_return_tenant_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260916_fiscal_year_close_guard"
down_revision = "20260916_tax_return_tenant_integrity"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION prevent_fiscal_year_close_with_unposted_entries()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.status = 'closed' AND OLD.status IS DISTINCT FROM 'closed' THEN
                IF EXISTS (
                    SELECT 1
                    FROM journal_entries e
                    WHERE e.tenant_id = NEW.tenant_id
                      AND e.company_id = NEW.company_id
                      AND e.fiscal_year_id = NEW.id
                      AND e.status IN ('draft', 'pending', 'approved')
                ) THEN
                    RAISE EXCEPTION
                        'Cannot close fiscal year %: unposted journal entries remain',
                        NEW.id
                        USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;
    """))
    conn.execute(sa.text("""
        DROP TRIGGER IF EXISTS trg_fiscal_year_close_unposted_guard
        ON fiscal_years;
        CREATE TRIGGER trg_fiscal_year_close_unposted_guard
        BEFORE UPDATE OF status ON fiscal_years
        FOR EACH ROW
        EXECUTE FUNCTION prevent_fiscal_year_close_with_unposted_entries();
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DROP TRIGGER IF EXISTS trg_fiscal_year_close_unposted_guard
        ON fiscal_years;
    """))
    conn.execute(sa.text("""
        DROP FUNCTION IF EXISTS prevent_fiscal_year_close_with_unposted_entries();
    """))
