"""add commercial rentals to the SaaS module catalog
Revision ID: 20260921_rentals_module_catalog
Revises: 20260921_rentals_core
"""
from alembic import op
import sqlalchemy as sa
revision="20260921_rentals_module_catalog"
down_revision="20260921_rentals_core"
branch_labels=None
depends_on=None
def upgrade():
    conn=op.get_bind()
    conn.execute(sa.text("""INSERT INTO system_modules (code,name_ar,name_en,description_ar,description_en,is_core,is_active,display_order,created_at)
    VALUES ('rentals','التأجير التجاري','Commercial Leasing','إدارة العقود والوحدات والإيجارات التجارية','Commercial leasing, contracts, units and charges',false,true,90,now())
    ON CONFLICT (code) DO UPDATE SET is_active=true,name_ar=EXCLUDED.name_ar,name_en=EXCLUDED.name_en,display_order=EXCLUDED.display_order"""))
    conn.execute(sa.text("""INSERT INTO plan_modules (plan_id,module_id,is_enabled)
    SELECT p.id,m.id,true FROM subscription_plans p CROSS JOIN system_modules m
    WHERE m.code='rentals' AND p.is_active=true AND NOT EXISTS
    (SELECT 1 FROM plan_modules pm WHERE pm.plan_id=p.id AND pm.module_id=m.id)"""))
def downgrade():
    conn=op.get_bind()
    conn.execute(sa.text("DELETE FROM plan_modules WHERE module_id IN (SELECT id FROM system_modules WHERE code='rentals')"))
    conn.execute(sa.text("DELETE FROM system_modules WHERE code='rentals'"))
