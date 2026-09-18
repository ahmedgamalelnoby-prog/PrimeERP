"""Add Salla public-app installation, token, subscription and SSO state.

Revision ID: 20260919_salla_public_app
Revises: 20260919_shipping_withdrawal_fee_default
"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_salla_public_app"
down_revision = "20260919_shipping_withdrawal_fee_default"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "salla_app_installations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.String(160), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("integration_connections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("access_token_ciphertext", sa.Text(), nullable=False),
        sa.Column("refresh_token_ciphertext", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(30), nullable=False, server_default="bearer"),
        sa.Column("store_name", sa.String(255), nullable=True),
        sa.Column("store_domain", sa.String(500), nullable=True),
        sa.Column("merchant_email", sa.String(320), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("subscription_status", sa.String(30), nullable=True),
        sa.Column("subscription_id", sa.String(160), nullable=True),
        sa.Column("subscription_item_slug", sa.String(160), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_webhook_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("merchant_id", name="uq_salla_app_installation_merchant"),
        sa.UniqueConstraint("connection_id", name="uq_salla_app_installation_connection"),
    )
    op.create_index("ix_salla_app_installations_merchant_id", "salla_app_installations", ["merchant_id"])
    op.create_index("ix_salla_app_installations_tenant_id", "salla_app_installations", ["tenant_id"])
    op.create_index("ix_salla_app_installations_company_id", "salla_app_installations", ["company_id"])
    op.create_index("ix_salla_app_installations_user_id", "salla_app_installations", ["user_id"])
    op.create_index("ix_salla_app_installations_status", "salla_app_installations", ["status"])
    op.create_index("ix_salla_app_installations_subscription_status", "salla_app_installations", ["subscription_status"])

    op.create_table(
        "salla_sso_tickets",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("installation_id", sa.Integer(), sa.ForeignKey("salla_app_installations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_salla_sso_tickets_installation_id", "salla_sso_tickets", ["installation_id"])
    op.create_index("ix_salla_sso_tickets_tenant_id", "salla_sso_tickets", ["tenant_id"])
    op.create_index("ix_salla_sso_tickets_user_id", "salla_sso_tickets", ["user_id"])
    op.create_index("ix_salla_sso_tickets_expires_at", "salla_sso_tickets", ["expires_at"])


def downgrade() -> None:
    op.drop_table("salla_sso_tickets")
    op.drop_table("salla_app_installations")
