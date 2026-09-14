"""report worker locking and attempt idempotency

Revision ID: 20260915_report_attempt_locking
Revises: 20260915_tax_return_drafts
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_report_attempt_locking"
down_revision = "20260915_tax_return_drafts"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("report_delivery_attempts", sa.Column("locked_at", sa.DateTime(timezone=True)))
    op.add_column("report_delivery_attempts", sa.Column("locked_by", sa.String(100)))
    op.create_unique_constraint("uq_report_delivery_attempt_no", "report_delivery_attempts", ["delivery_id", "attempt_no"])


def downgrade():
    op.drop_constraint("uq_report_delivery_attempt_no", "report_delivery_attempts", type_="unique")
    op.drop_column("report_delivery_attempts", "locked_by")
    op.drop_column("report_delivery_attempts", "locked_at")
