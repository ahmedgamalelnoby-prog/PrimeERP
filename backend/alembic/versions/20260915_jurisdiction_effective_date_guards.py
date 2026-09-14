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
        "company_id, jurisdiction_id, role",
        "company_jurisdiction_effective_no_overlap",
    ),
    (
        "partner_jurisdictions",
        "partner_id, jurisdiction_id, role",
        "partner_jurisdiction_effective_no_overlap",
    ),
    (
        "jurisdiction_tax_rules",
        "jurisdiction_id, code",
        "jurisdiction_tax_rule_effective_no_overlap",
    ),
)


def _assert_no_invalid_or_overlapping_rows(table: str, key_sql: str) -> None:
    op.execute(
        f"""
        DO $$
        DECLARE
            invalid_count integer;
            overlap_key text;
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

            SELECT string_agg(row_key, '; ' ORDER BY row_key)
            INTO overlap_key
            FROM (
                SELECT DISTINCT
                    format('key=%s ids=%s,%s',
                        ({key_sql})::text,
                        a.id,
                        b.id
                    ) AS row_key
                FROM {table} a
                JOIN {table} b
                  ON a.id < b.id
                 AND a.is_active
                 AND b.is_active
                 AND ({key_sql.replace('effective_', 'a.effective_')}) = ({key_sql.replace('effective_', 'b.effective_')})
                 AND daterange(
                        a.effective_from,
                        COALESCE(a.effective_to + 1, 'infinity'::date),
                        '[)'
                     ) && daterange(
                        b.effective_from,
                        COALESCE(b.effective_to + 1, 'infinity'::date),
                        '[)'
                     )
                LIMIT 10
            ) conflicts;

            IF overlap_key IS NOT NULL THEN
                RAISE EXCEPTION
                    'Cannot add effective-date guard on {table}: active effective-date overlaps exist: %',
                    overlap_key;
            END IF;
        END $$;
        """
    )


def upgrade():
    # btree_gist supplies GiST equality operator classes for int/text columns,
    # allowing them to participate in the same exclusion constraint as the date range.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    for table, key_sql, _ in _TABLES:
        _assert_no_invalid_or_overlapping_rows(table, key_sql)

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
            daterange(
                effective_from,
                COALESCE(effective_to + 1, 'infinity'::date),
                '[)'
            ) WITH &&
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
            daterange(
                effective_from,
                COALESCE(effective_to + 1, 'infinity'::date),
                '[)'
            ) WITH &&
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
            daterange(
                effective_from,
                COALESCE(effective_to + 1, 'infinity'::date),
                '[)'
            ) WITH &&
        ) WHERE (is_active)
        """
    )


def downgrade():
    op.execute(
        "ALTER TABLE jurisdiction_tax_rules DROP CONSTRAINT IF EXISTS jurisdiction_tax_rule_effective_no_overlap"
    )
    op.execute(
        "ALTER TABLE partner_jurisdictions DROP CONSTRAINT IF EXISTS partner_jurisdiction_effective_no_overlap"
    )
    op.execute(
        "ALTER TABLE company_jurisdictions DROP CONSTRAINT IF EXISTS company_jurisdiction_effective_no_overlap"
    )
    op.execute(
        "ALTER TABLE jurisdiction_tax_rules DROP CONSTRAINT IF EXISTS ck_jurisdiction_tax_rule_effective_dates"
    )
    op.execute(
        "ALTER TABLE partner_jurisdictions DROP CONSTRAINT IF EXISTS ck_partner_jurisdiction_effective_dates"
    )
    op.execute(
        "ALTER TABLE company_jurisdictions DROP CONSTRAINT IF EXISTS ck_company_jurisdiction_effective_dates"
    )
