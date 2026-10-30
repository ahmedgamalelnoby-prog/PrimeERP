"""Merge the global user identity uniqueness migration with the Odoo catalog lineage.

Revision ID: 20261108_merge_global_user_identity_heads
Revises: d8f77511bacb, 20261107_global_user_identity_uniqueness
Create Date: 2026-10-30
"""

from __future__ import annotations

revision = "20261108_merge_global_user_identity_heads"
down_revision = ("d8f77511bacb", "20261107_global_user_identity_uniqueness")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Structural merge only. Both parent migrations own their respective changes.
    pass


def downgrade() -> None:
    # Structural merge only; no schema or data changes to reverse.
    pass
