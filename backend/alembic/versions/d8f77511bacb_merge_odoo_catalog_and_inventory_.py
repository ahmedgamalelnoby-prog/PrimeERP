"""merge odoo catalog and inventory approval heads

Revision ID: d8f77511bacb
Revises: 20260911_odoo_module_catalog, 20261106_merge_inventory_approval_heads
Create Date: 2026-10-27 19:48:43.735844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f77511bacb'
down_revision: Union[str, None] = ('20260911_odoo_module_catalog', '20261106_merge_inventory_approval_heads')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
