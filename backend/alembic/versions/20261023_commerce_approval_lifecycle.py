"""Add auditable approval states for sales and purchase orders.

Revision ID: 20261023_commerce_approval_lifecycle
Revises: 20261022_purchase_order_line_links
"""
from alembic import op
import sqlalchemy as sa

revision = "20261023_commerce_approval_lifecycle"
down_revision = "20261022_purchase_order_line_links"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sales_documents") as batch:
        batch.drop_constraint("ck_sales_document_status", type_="check")
        batch.create_check_constraint(
            "ck_sales_document_status",
            "status IN ('draft','pending_approval','approved','rejected','confirmed','partially_fulfilled','fulfilled','cancelled','posted')",
        )
    with op.batch_alter_table("purchase_documents") as batch:
        batch.drop_constraint("ck_purchase_document_status", type_="check")
        batch.create_check_constraint(
            "ck_purchase_document_status",
            "status IN ('draft','pending_approval','approved','rejected','confirmed','partially_received','received','cancelled','posted')",
        )

    op.create_table(
        "commerce_approval_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_kind", sa.String(length=12), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("document_kind IN ('sale','purchase')", name="ck_commerce_approval_event_kind"),
        sa.CheckConstraint("action IN ('submitted','approved','rejected')", name="ck_commerce_approval_event_action"),
    )
    op.create_index("ix_commerce_approval_events_company_id", "commerce_approval_events", ["company_id"])
    op.create_index("ix_commerce_approval_events_document_id", "commerce_approval_events", ["document_id"])
    op.create_index("ix_commerce_approval_events_actor_id", "commerce_approval_events", ["actor_id"])
    op.create_index(
        "ix_commerce_approval_document_timeline",
        "commerce_approval_events",
        ["company_id", "document_kind", "document_id", "id"],
    )


def downgrade():
    op.drop_index("ix_commerce_approval_document_timeline", table_name="commerce_approval_events")
    op.drop_index("ix_commerce_approval_events_actor_id", table_name="commerce_approval_events")
    op.drop_index("ix_commerce_approval_events_document_id", table_name="commerce_approval_events")
    op.drop_index("ix_commerce_approval_events_company_id", table_name="commerce_approval_events")
    op.drop_table("commerce_approval_events")

    with op.batch_alter_table("purchase_documents") as batch:
        batch.drop_constraint("ck_purchase_document_status", type_="check")
        batch.create_check_constraint(
            "ck_purchase_document_status",
            "status IN ('draft','confirmed','partially_received','received','cancelled','posted')",
        )
    with op.batch_alter_table("sales_documents") as batch:
        batch.drop_constraint("ck_sales_document_status", type_="check")
        batch.create_check_constraint(
            "ck_sales_document_status",
            "status IN ('draft','confirmed','partially_fulfilled','fulfilled','cancelled','posted')",
        )
