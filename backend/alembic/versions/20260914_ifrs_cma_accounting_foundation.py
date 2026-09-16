"""IFRS/CMA accounting foundation graph marker.

Revision ID: 20260914_ifrs_cma_accounting_foundation
Revises: 20260914_namespace_integration_product_mapping_external_ids

PrimeERP already has a canonical accounting foundation. This historical
revision previously created a parallel accounting schema and could fail with
DuplicateTable when canonical tables already existed. It is therefore kept as
an Alembic graph marker only; canonical accounting structures are managed by
their dedicated migrations.
"""

revision = "20260914_ifrs_cma_accounting_foundation"
down_revision = "20260914_namespace_integration_product_mapping_external_ids"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
