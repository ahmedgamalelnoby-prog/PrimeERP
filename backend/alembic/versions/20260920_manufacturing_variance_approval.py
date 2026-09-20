"""Allow manufacturing variance journals to await independent approval."""
from alembic import op

revision = "20260920_manufacturing_variance_approval"
down_revision = (
    "20260920_pos_session_sales_link",
    "20260920_enterprise_payroll_period_guard",
)
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_mfg_variance_status", "manufacturing_variances", type_="check")
    op.create_check_constraint(
        "ck_mfg_variance_status",
        "manufacturing_variances",
        "status IN ('calculated','pending_approval','posted','reversed')",
    )


def downgrade():
    op.drop_constraint("ck_mfg_variance_status", "manufacturing_variances", type_="check")
    op.create_check_constraint(
        "ck_mfg_variance_status",
        "manufacturing_variances",
        "status IN ('calculated','posted','reversed')",
    )
