"""Normalize provider-specific shipping carrier mappings to the generic entity type.

Revision ID: 20260919_generic_shipping_mapping
Revises: 20260919_industry_profile
"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_generic_shipping_mapping"
down_revision = "20260919_industry_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    # Existing Salla installations keep their mapping; only the semantic
    # namespace changes. Provider identity remains in connection.provider.
    conn.execute(sa.text("""
        UPDATE integration_mappings
        SET entity_type = 'shipping_carrier'
        WHERE entity_type = 'salla_shipping_company'
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE integration_mappings
        SET entity_type = 'salla_shipping_company'
        WHERE entity_type = 'shipping_carrier'
          AND connection_id IN (
              SELECT id FROM integration_connections WHERE provider = 'salla'
          )
    """))
