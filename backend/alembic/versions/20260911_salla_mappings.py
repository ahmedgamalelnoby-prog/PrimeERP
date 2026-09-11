"""add Salla external entity mappings

Revision ID: 20260911_salla_mappings
Revises: 20260911_commerce_payment_idempotency
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_salla_mappings"
down_revision = "20260911_commerce_payment_idempotency"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "salla_external_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("external_id", sa.String(length=160), nullable=False),
        sa.Column("internal_id", sa.Integer(), nullable=True),
        sa.Column("external_version", sa.String(length=80), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "entity_type", "external_id", name="uq_salla_mapping_connection_entity_external"),
    )
    op.create_index("ix_salla_external_mappings_company_id", "salla_external_mappings", ["company_id"])
    op.create_index("ix_salla_external_mappings_connection_id", "salla_external_mappings", ["connection_id"])


def downgrade():
    op.drop_index("ix_salla_external_mappings_connection_id", table_name="salla_external_mappings")
    op.drop_index("ix_salla_external_mappings_company_id", table_name="salla_external_mappings")
    op.drop_table("salla_external_mappings")
