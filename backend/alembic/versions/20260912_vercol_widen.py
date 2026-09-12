"""widen Alembic version column for long release revision identifiers

The original Alembic bootstrap created ``alembic_version.version_num`` as
VARCHAR(32). PrimeERP revision identifiers are longer than that, so the
version table itself must be widened before those revisions can be recorded.

Revision ID: 20260912_vercol_widen
Revises: 20260912_uom_constraints
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_vercol_widen"
down_revision = "20260912_uom_constraints"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=255),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
