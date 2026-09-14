"""durable report scheduler leases and delivery idempotency

Revision ID: 20260915_report_scheduler_leases
Revises: 20260915_merge_reporting_heads
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_report_scheduler_leases"
down_revision = "20260915_merge_reporting_heads"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("report_deliveries", sa.Column("locked_until", sa.DateTime(timezone=True)))
    op.add_column("report_deliveries", sa.Column("locked_by", sa.String(100)))
    op.add_column("report_deliveries", sa.Column("delivery_key", sa.String(255)))
    op.create_index("ix_report_deliveries_locked_until", "report_deliveries", ["locked_until"])
    op.create_index("ix_report_deliveries_delivery_key", "report_deliveries", ["delivery_key"])
    op.create_unique_constraint("uq_report_deliveries_delivery_key", "report_deliveries", ["delivery_key"])


def downgrade():
    op.drop_constraint("uq_report_deliveries_delivery_key", "report_deliveries", type_="unique")
    op.drop_index("ix_report_deliveries_delivery_key", table_name="report_deliveries")
    op.drop_index("ix_report_deliveries_locked_until", table_name="report_deliveries")
    op.drop_column("report_deliveries", "delivery_key")
    op.drop_column("report_deliveries", "locked_by")
    op.drop_column("report_deliveries", "locked_until")
