"""Add legal/tax identity and ETA linkage fields.
Revision ID: 20260923_legal_tax_eta_identity
Revises: 20260920_pos_outlet_routing (which already includes enterprise finance ancestry)
"""
from alembic import op
import sqlalchemy as sa

revision = "20260923_legal_tax_eta_identity"
down_revision = "20260920_pos_outlet_routing"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("companies", sa.Column("legal_name", sa.String(200), nullable=True))
    op.add_column("companies", sa.Column("commercial_registration_number", sa.String(100), nullable=True))
    op.add_column("companies", sa.Column("tax_authority", sa.String(150), nullable=True))
    op.add_column("companies", sa.Column("eta_registration_status", sa.String(30), nullable=False, server_default="not_configured"))
    op.add_column("companies", sa.Column("eta_taxpayer_id", sa.String(100), nullable=True))
    op.add_column("companies", sa.Column("eta_last_verified_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_index("ix_companies_commercial_registration_number", "companies", ["commercial_registration_number"])
    op.create_index("ix_companies_eta_taxpayer_id", "companies", ["eta_taxpayer_id"])

    op.add_column("commerce_partners", sa.Column("commercial_registration_number", sa.String(100), nullable=True))
    op.add_column("commerce_partners", sa.Column("tax_authority", sa.String(150), nullable=True))
    op.add_column("commerce_partners", sa.Column("eta_registration_status", sa.String(30), nullable=False, server_default="not_configured"))
    op.add_column("commerce_partners", sa.Column("eta_party_id", sa.String(100), nullable=True))
    op.add_column("commerce_partners", sa.Column("eta_last_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_commerce_partners_commercial_registration_number", "commerce_partners", ["commercial_registration_number"])
    op.create_index("ix_commerce_partners_eta_party_id", "commerce_partners", ["eta_party_id"])

def downgrade():
    op.drop_index("ix_commerce_partners_eta_party_id", table_name="commerce_partners")
    op.drop_index("ix_commerce_partners_commercial_registration_number", table_name="commerce_partners")
    op.drop_column("commerce_partners", "eta_last_verified_at")
    op.drop_column("commerce_partners", "eta_party_id")
    op.drop_column("commerce_partners", "eta_registration_status")
    op.drop_column("commerce_partners", "tax_authority")
    op.drop_column("commerce_partners", "commercial_registration_number")
    op.drop_index("ix_companies_eta_taxpayer_id", table_name="companies")
    op.drop_index("ix_companies_commercial_registration_number", table_name="companies")
    op.drop_column("companies", "eta_last_verified_at")
    op.drop_column("companies", "eta_taxpayer_id")
    op.drop_column("companies", "eta_registration_status")
    op.drop_column("companies", "tax_authority")
    op.drop_column("companies", "commercial_registration_number")
    op.drop_column("companies", "legal_name")
