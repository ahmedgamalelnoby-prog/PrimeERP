"""Register Shipping & Logistics in the platform module catalog."""
from alembic import op

revision = "20260911shippingcatalog"
down_revision = "20260911shipping"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO system_modules (code, name_ar, name_en, description_ar, description_en, is_core, is_active, display_order)
        VALUES ('SHP', 'الشحن واللوجستيات', 'Shipping & Logistics', 'شركات الشحن والتتبع وCOD والتسويات والتكاملات', 'Shipping providers, tracking, COD, settlements and integrations', false, true, 90)
        ON CONFLICT (code) DO NOTHING
    """)


def downgrade():
    op.execute("DELETE FROM system_modules WHERE code = 'SHP'")
