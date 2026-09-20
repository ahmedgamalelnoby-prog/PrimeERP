"""Cost-layer completion migration marker. The canonical inventory_cost_layers table is owned by inventory stock-move persistence."""
from alembic import op
revision="20260920_inventory_cost_layers"
down_revision="20260920_accounting_automation"
branch_labels=None
depends_on=None
def upgrade():
    pass
def downgrade():
    pass
