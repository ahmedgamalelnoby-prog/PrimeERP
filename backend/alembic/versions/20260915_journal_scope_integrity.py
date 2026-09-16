"""Enforce tenant/company scope on journal entry lines.

Revision ID: 20260915_journal_scope_integrity
Revises: 20260915_tax_rate_domain_hardening

This revision must coexist with the canonical accounting keys created by
older migrations; upgrade therefore reuses an existing compatible unique key.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_journal_scope_integrity"
down_revision = "20260915_tax_rate_domain_hardening"
branch_labels = None
depends_on = None


def _assert_clean(conn, sql: str, message: str) -> None:
    if conn.execute(sa.text(sql)).scalar():
        raise RuntimeError(message)


def _has_unique_key(conn, table: str, columns: list[str]) -> bool:
    """Return True when the table already has an exact usable unique key.

    PostgreSQL catalog attributes use the `name` type. Explicitly cast
    attname to text before array aggregation so the resulting `text[]` can
    safely be compared with the supplied `text[]` parameter.
    """
    result = conn.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                WHERE n.nspname = current_schema()
                  AND t.relname = :table_name
                  AND c.contype IN ('p', 'u')
                  AND (
                      SELECT array_agg(a.attname::text ORDER BY k.ord)
                      FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
                      JOIN pg_attribute a
                        ON a.attrelid = t.oid
                       AND a.attnum = k.attnum
                  ) = CAST(:columns AS text[])
            )
            OR EXISTS (
                SELECT 1
                FROM pg_index i
                JOIN pg_class t ON t.oid = i.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                WHERE n.nspname = current_schema()
                  AND t.relname = :table_name
                  AND i.indisunique
                  AND i.indisvalid
                  AND i.indpred IS NULL
                  AND (
                      SELECT array_agg(a.attname::text ORDER BY k.ord)
                      FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum, ord)
                      JOIN pg_attribute a
                        ON a.attrelid = t.oid
                       AND a.attnum = k.attnum
                  ) = CAST(:columns AS text[])
            )
            """
        ),
        {"table_name": table, "columns": "{" + ",".join(columns) + "}"},
    )
    return bool(result.scalar())


def _relation_exists(conn, name: str) -> bool:
    return bool(
        conn.execute(
            sa.text("SELECT to_regclass(:name) IS NOT NULL"),
            {"name": name},
        ).scalar()
    )


def _ensure_unique_key(conn, table: str, columns: list[str], preferred_name: str) -> None:
    if _has_unique_key(conn, table, columns):
        return

    name = preferred_name
    if _relation_exists(conn, name):
        name = f"{preferred_name}_scope"
        if _relation_exists(conn, name):
            raise RuntimeError(
                f"Cannot create required unique key on {table}: relations '{preferred_name}' and '{name}' already exist."
            )

    op.create_unique_constraint(name, table, columns)


def _drop_constraint_if_exists(conn, name: str, table: str, type_: str) -> None:
    exists = conn.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                WHERE n.nspname = current_schema()
                  AND t.relname = :table_name
                  AND c.conname = :constraint_name
            )
            """
        ),
        {"table_name": table, "constraint_name": name},
    ).scalar()
    if exists:
        op.drop_constraint(name, table, type_=type_)


def upgrade():
    conn = op.get_bind()

    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines l JOIN journal_entries e ON e.id = l.entry_id WHERE l.tenant_id <> e.tenant_id)",
        "Cannot harden journal_entry_lines: tenant scope does not match parent entry.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines l JOIN journal_entries e ON e.id = l.entry_id JOIN account_combinations a ON a.id = l.account_combination_id WHERE e.company_id <> a.company_id)",
        "Cannot harden journal_entry_lines: account combination belongs to another company.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines l JOIN journal_entries e ON e.id = l.entry_id JOIN accounting_departments d ON d.id = l.department_id WHERE l.department_id IS NOT NULL AND e.company_id <> d.company_id)",
        "Cannot harden journal_entry_lines: department belongs to another company.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines l JOIN journal_entries e ON e.id = l.entry_id JOIN accounting_cost_centers c ON c.id = l.cost_center_id WHERE l.cost_center_id IS NOT NULL AND e.company_id <> c.company_id)",
        "Cannot harden journal_entry_lines: cost center belongs to another company.",
    )

    op.add_column("journal_entry_lines", sa.Column("company_id", sa.Integer(), nullable=True))
    conn.execute(
        sa.text(
            "UPDATE journal_entry_lines l SET company_id = e.company_id "
            "FROM journal_entries e WHERE e.id = l.entry_id"
        )
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM journal_entry_lines WHERE company_id IS NULL)",
        "Cannot harden journal_entry_lines: company could not be derived from parent entry.",
    )
    op.alter_column("journal_entry_lines", "company_id", nullable=False)
    op.create_index(
        "ix_journal_line_company_entry",
        "journal_entry_lines",
        ["company_id", "entry_id"],
    )

    _ensure_unique_key(
        conn,
        "journal_entries",
        ["tenant_id", "company_id", "id"],
        "uq_journal_entries_tenant_company_id",
    )
    _ensure_unique_key(
        conn,
        "account_combinations",
        ["company_id", "id"],
        "uq_account_combinations_company_id",
    )

    op.create_foreign_key(
        "fk_journal_line_entry_same_scope",
        "journal_entry_lines",
        "journal_entries",
        ["tenant_id", "company_id", "entry_id"],
        ["tenant_id", "company_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_journal_line_account_same_company",
        "journal_entry_lines",
        "account_combinations",
        ["company_id", "account_combination_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_journal_line_department_same_company",
        "journal_entry_lines",
        "accounting_departments",
        ["company_id", "department_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_journal_line_cost_center_same_company",
        "journal_entry_lines",
        "accounting_cost_centers",
        ["company_id", "cost_center_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )

    op.create_check_constraint(
        "ck_journal_line_base_amounts_nonnegative",
        "journal_entry_lines",
        "base_debit >= 0 AND base_credit >= 0",
    )


def downgrade():
    conn = op.get_bind()
    _drop_constraint_if_exists(
        conn,
        "ck_journal_line_base_amounts_nonnegative",
        "journal_entry_lines",
        "check",
    )
    _drop_constraint_if_exists(
        conn,
        "fk_journal_line_cost_center_same_company",
        "journal_entry_lines",
        "foreignkey",
    )
    _drop_constraint_if_exists(
        conn,
        "fk_journal_line_department_same_company",
        "journal_entry_lines",
        "foreignkey",
    )
    _drop_constraint_if_exists(
        conn,
        "fk_journal_line_account_same_company",
        "journal_entry_lines",
        "foreignkey",
    )
    _drop_constraint_if_exists(
        conn,
        "fk_journal_line_entry_same_scope",
        "journal_entry_lines",
        "foreignkey",
    )
    op.drop_index(
        "ix_journal_line_company_entry",
        table_name="journal_entry_lines",
        if_exists=True,
    )
    op.drop_column("journal_entry_lines", "company_id")
