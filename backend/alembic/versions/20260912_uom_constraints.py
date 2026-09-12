"""enforce one active base UOM per company/category

Revision ID: 20260912_uom_constraints
Revises: 20260912_commerce_idempotency
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_uom_constraints"
down_revision = "20260912_commerce_idempotency"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_units_of_measure_active_base_category",
        "units_of_measure",
        ["company_id", "category"],
        unique=True,
        postgresql_where=sa.text("is_base = true AND is_active = true"),
    )


def downgrade():
    op.drop_index("uq_units_of_measure_active_base_category", table_name="units_of_measure")
