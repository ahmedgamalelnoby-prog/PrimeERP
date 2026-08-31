"""seed configurable SaaS defaults

Revision ID: 20260901defaults
Revises: 20260901saas
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260901defaults"
down_revision: Union[str, Sequence[str], None] = "20260901saas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO platform_settings (key, value, description, is_public)
        VALUES ('default_trial_days', '14', 'Default free trial duration in days', false)
        ON CONFLICT (key) DO NOTHING
    """))
    op.execute(sa.text("""
        INSERT INTO platform_settings (key, value, description, is_public)
        VALUES ('default_grace_period_days', '7', 'Default subscription grace period in days', false)
        ON CONFLICT (key) DO NOTHING
    """))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM platform_settings WHERE key IN ('default_trial_days','default_grace_period_days')"))
