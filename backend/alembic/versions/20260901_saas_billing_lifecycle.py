"""add billing, pricing, payments and subscription lifecycle schema

Revision ID: 20260901saas
Revises: 20260831legal
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260901saas"
down_revision: Union[str, Sequence[str], None] = "20260831legal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("key", name="uq_platform_setting_key"),
    )

    op.create_table(
        "module_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="EGP"),
        sa.Column("monthly_base_price", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("yearly_base_price", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("monthly_user_price", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("yearly_user_price", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["module_id"], ["system_modules.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("module_id", "currency_code", name="uq_module_price_currency"),
        sa.CheckConstraint("monthly_base_price >= 0", name="ck_module_price_monthly_base"),
        sa.CheckConstraint("yearly_base_price >= 0", name="ck_module_price_yearly_base"),
        sa.CheckConstraint("monthly_user_price >= 0", name="ck_module_price_monthly_user"),
        sa.CheckConstraint("yearly_user_price >= 0", name="ck_module_price_yearly_user"),
    )
    op.create_index("ix_module_prices_module_id", "module_prices", ["module_id"])

    op.create_table(
        "subscription_modules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("price_override", sa.Numeric(18, 2), nullable=True),
        sa.Column("discount_percent", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["system_modules.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("subscription_id", "module_id", name="uq_subscription_module"),
        sa.CheckConstraint("discount_percent >= 0 AND discount_percent <= 100", name="ck_subscription_module_discount"),
    )
    op.create_index("ix_subscription_modules_subscription_id", "subscription_modules", ["subscription_id"])
    op.create_index("ix_subscription_modules_module_id", "subscription_modules", ["module_id"])

    op.create_table(
        "discounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("discount_type", sa.String(20), nullable=False, server_default="percentage"),
        sa.Column("value", sa.Numeric(18, 2), nullable=False),
        sa.Column("scope", sa.String(30), nullable=False, server_default="global"),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("module_id", sa.Integer(), nullable=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["module_id"], ["system_modules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.CheckConstraint("value >= 0", name="ck_discount_value"),
        sa.CheckConstraint("used_count >= 0", name="ck_discount_used_count"),
    )
    op.create_index("ix_discounts_code", "discounts", ["code"], unique=True)
    op.create_index("ix_discounts_active_dates", "discounts", ["is_active", "starts_at", "ends_at"])

    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discount_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["discount_id"], ["discounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("code", name="uq_offer_code"),
    )

    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("discount_id", sa.Integer(), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["discount_id"], ["discounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("code", name="uq_coupon_code"),
    )

    op.create_table(
        "bank_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bank_name", sa.String(150), nullable=False),
        sa.Column("account_name", sa.String(200), nullable=False),
        sa.Column("account_number", sa.String(100), nullable=True),
        sa.Column("iban", sa.String(100), nullable=True),
        sa.Column("swift", sa.String(30), nullable=True),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="EGP"),
        sa.Column("instructions_ar", sa.Text(), nullable=True),
        sa.Column("instructions_en", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="issued"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("invoice_number", name="uq_invoice_number"),
    )
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])

    op.create_table(
        "payment_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("bank_account_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=False, server_default="bank_transfer"),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("proof_file", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_payment_requests_tenant_id", "payment_requests", ["tenant_id"])
    op.create_index("ix_payment_requests_status", "payment_requests", ["status"])

    op.create_table(
        "subscription_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=True),
        sa.Column("to_status", sa.String(30), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_subscription_events_subscription_id", "subscription_events", ["subscription_id"])
    op.create_index("ix_subscription_events_tenant_id", "subscription_events", ["tenant_id"])


def downgrade() -> None:
    for name, table in [
        ("ix_subscription_events_tenant_id", "subscription_events"),
        ("ix_subscription_events_subscription_id", "subscription_events"),
    ]:
        op.drop_index(name, table_name=table)
    op.drop_table("subscription_events")
    op.drop_index("ix_payment_requests_status", table_name="payment_requests")
    op.drop_index("ix_payment_requests_tenant_id", table_name="payment_requests")
    op.drop_table("payment_requests")
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_tenant_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_table("bank_accounts")
    op.drop_table("coupons")
    op.drop_table("offers")
    op.drop_index("ix_discounts_active_dates", table_name="discounts")
    op.drop_index("ix_discounts_code", table_name="discounts")
    op.drop_table("discounts")
    op.drop_index("ix_subscription_modules_module_id", table_name="subscription_modules")
    op.drop_index("ix_subscription_modules_subscription_id", table_name="subscription_modules")
    op.drop_table("subscription_modules")
    op.drop_index("ix_module_prices_module_id", table_name="module_prices")
    op.drop_table("module_prices")
    op.drop_table("platform_settings")
