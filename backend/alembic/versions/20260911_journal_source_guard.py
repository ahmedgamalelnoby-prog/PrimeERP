"""add database idempotency guard for sourced journal entries

Revision ID: 20260911_journal_source_guard
Revises: 20260911_enterprise_rbac
"""
from alembic import op

revision = "20260911_journal_source_guard"
down_revision = "20260911_enterprise_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_journal_entry_source_idempotency",
        "journal_entries",
        ["tenant_id", "company_id", "source_module", "source_entity", "source_id"],
        unique=True,
        postgresql_where=(
            "source_module IS NOT NULL AND source_entity IS NOT NULL AND source_id IS NOT NULL"
        ),
    )


def downgrade():
    op.drop_index("uq_journal_entry_source_idempotency", table_name="journal_entries")
