"""database-level guards for effective-dated jurisdiction versions

Revision ID: 20260915_jurisdiction_effective_date_guards
Revises: 20260914_tax_snapshots
"""
from alembic import op

revision = "20260915_jurisdiction_effective_date_guards"
down_revision = "20260914_tax_snapshots"
branch_labels = None
depends_on = None

_TABLES = (
    (
        "company_jurisdictions",
        "a.company_id = b.company_id AND a.jurisdiction_id = b.jurisdiction_id AND a.role = b.role",
    ),
    (
        "partner_jurisdictions",
        "a.partner_id = b.partner_id AND a.jurisdiction_id = b.jurisdiction_id AND a.role = b.role",
    ),
    (
        "jurisdiction_tax_rules",
        "a.jurisdiction_id = b.jurisdiction_id AND a.code = b.code",
    ),
)


def _assert_clean(table: str, identity_sql: str) -> None:
    op.execute(
        f"""
        DO $$
        DECLARE invalid_count integer;
        DECLARE overlap_key text;
        BEGIN
            SELECT count(*) INTO invalid_count
            FROM {table}
            WHERE effective_to IS NOT NULL
              AND effective_to < effective_from;
            IF invalid_count > 0 THEN
                RAISE EXCEPTION
                    'Cannot add effective-date guard on {table}: % row(s) have effective_to before effective_from',
                    invalid_count;
            END IF;

            SELECT string_agg(format('ids=%s,%s', a.id, b.id), '; ')
            INTO overlap_key
            FROM {table} a
            JOIN {table} b
              ON a.id < b.id
             AND a.is_active
             AND b.is_active
             AND {identity_sql}
             AND daterange(a.effective_from, COALESCE(a.effective_to + 1, 'infinity'::date), '[)')
                 && daterange(b.effective_from, COALESCE(b.effective_to + 1, 'infinity'::date), '[)')
            LIMIT 10;

            IF overlap_key IS NOT NULL THEN
                RAISE EXCEPTION
                    'Cannot add effective-date guard on {table}: active overlaps exist: %',
                    overlap_key;
            END IF;
        END $$;
        """
    )


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    for table, identity_sql in _TABLES:
        _assert_clean(table, identity_sql)

    op.execute(
        """
        ALTER TABLE company_jurisdictions
        ADD CONSTRAINT ck_company_jurisdiction_effective_dates
        CHECK (effective_to IS NULL OR effective_to >= effective_from)
        """
    )
    op.execute(
        """
        ALTER TABLE partner_jurisdictions
        ADD CONSTRAINT ck_partner_jurisdiction_effective_dates
        CHECK (effective_to IS NULL OR effective_to >= effective_from)
        """
    )
    op.execute(
        """
        ALTER TABLE jurisdiction_tax_rules
        ADD CONSTRAINT ck_jurisdiction_tax_rule_effective_dates
        CHECK (effective_to IS NULL OR effective_to >= effective_from)
        """
    )

    op.execute(
        """
        ALTER TABLE company_jurisdictions
        ADD CONSTRAINT company_jurisdiction_effective_no_overlap
        EXCLUDE USING gist (
            company_id WITH =,
            jurisdiction_id WITH =,
            role WITH =,
            daterange(effective_from, COALESCE(effective_to + 1, 'infinity'::date), '[)') WITH &&
        ) WHERE (is_active)
        """
    )
    op.execute(
        """
        ALTER TABLE partner_jurisdictions
        ADD CONSTRAINT partner_jurisdiction_effective_no_overlap
        EXCLUDE USING gist (
            partner_id WITH =,
            jurisdiction_id WITH =,
            role WITH =,
            daterange(effective_from, COALESCE(effective_to + 1, 'infinity'::date), '[)') WITH &&
        ) WHERE (is_active)
        """
    )
    op.execute(
        """
        ALTER TABLE jurisdiction_tax_rules
        ADD CONSTRAINT jurisdiction_tax_rule_effective_no_overlap
        EXCLUDE USING gist (
            jurisdiction_id WITH =,
            code WITH =,
            daterange(effective_from, COALESCE(effective_to + 1, 'infinity'::date), '[)') WITH &&
        ) WHERE (is_active)
        """
    )


def downgrade():
    op.execute("ALTER TABLE jurisdiction_tax_rules DROP CONSTRAINT IF EXISTS jurisdiction_tax_rule_effective_no_overlap")
    op.execute("ALTER TABLE partner_jurisdictions DROP CONSTRAINT IF EXISTS partner_jurisdiction_effective_no_overlap")
    op.execute("ALTER TABLE company_jurisdictions DROP CONSTRAINT IF EXISTS company_jurisdiction_effective_no_overlap")
    op.execute("ALTER TABLE jurisdiction_tax_rules DROP CONSTRAINT IF EXISTS ck_jurisdiction_tax_rule_effective_dates")
    op.execute("ALTER TABLE partner_jurisdictions DROP CONSTRAINT IF EXISTS ck_partner_jurisdiction_effective_dates")
    op.execute("ALTER TABLE company_jurisdictions DROP CONSTRAINT IF EXISTS ck_company_jurisdiction_effective_dates")
