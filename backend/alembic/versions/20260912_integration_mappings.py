"""add provider entity mapping registry

Revision ID: 20260912_integration_mappings
Revises: 20260912_audit_rbac
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_integration_mappings"
down_revision = "20260912_audit_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "integration_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("external_id", sa.String(length=160), nullable=False),
        sa.Column("local_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("connection_id", "entity_type", "external_id", name="uq_integration_mapping_external"),
        sa.UniqueConstraint("connection_id", "entity_type", "local_id", name="uq_integration_mapping_local"),
    )
    op.create_index("ix_integration_mappings_company_id", "integration_mappings", ["company_id"])
    op.create_index("ix_integration_mappings_connection_id", "integration_mappings", ["connection_id"])
    op.create_index("ix_integration_mappings_entity_type", "integration_mappings", ["entity_type"])


def downgrade():
    for name in ("ix_integration_mappings_entity_type", "ix_integration_mappings_connection_id", "ix_integration_mappings_company_id"):
        op.drop_index(name, table_name="integration_mappings")
    op.drop_table("integration_mappings")
