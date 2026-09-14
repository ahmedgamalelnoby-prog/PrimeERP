"""idempotency constraints for ETA e-invoice documents

Revision ID: 20260915_einvoice_idempotency
Revises: 20260915_reporting_delivery
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_einvoice_idempotency"
down_revision = "20260915_reporting_delivery"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # Existing duplicates must be resolved explicitly instead of silently
    # changing their business meaning during deployment.
    for sql in (
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM (
                    SELECT company_id, source_type, source_id, count(*) c
                    FROM egyptian_einvoice_documents
                    GROUP BY company_id, source_type, source_id
                    HAVING count(*) > 1
                ) d
            ) THEN
                RAISE EXCEPTION 'Duplicate ETA source documents exist; resolve them before enabling idempotency';
            END IF;
        END $$;
        """,
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM (
                    SELECT submission_uuid, count(*) c
                    FROM egyptian_einvoice_documents
                    WHERE submission_uuid IS NOT NULL
                    GROUP BY submission_uuid
                    HAVING count(*) > 1
                ) d
            ) THEN
                RAISE EXCEPTION 'Duplicate ETA submission UUIDs exist; resolve them before enabling idempotency';
            END IF;
        END $$;
        """,
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM (
                    SELECT eta_uuid, count(*) c
                    FROM egyptian_einvoice_documents
                    WHERE eta_uuid IS NOT NULL
                    GROUP BY eta_uuid
                    HAVING count(*) > 1
                ) d
            ) THEN
                RAISE EXCEPTION 'Duplicate ETA document UUIDs exist; resolve them before enabling idempotency';
            END IF;
        END $$;
        """,
    ):
        bind.execute(sa.text(sql))
    op.create_unique_constraint("uq_eta_source_document", "egyptian_einvoice_documents", ["company_id", "source_type", "source_id"])
    op.create_unique_constraint("uq_eta_submission_uuid", "egyptian_einvoice_documents", ["submission_uuid"])
    op.create_unique_constraint("uq_eta_document_uuid", "egyptian_einvoice_documents", ["eta_uuid"])


def downgrade():
    op.drop_constraint("uq_eta_document_uuid", "egyptian_einvoice_documents", type_="unique")
    op.drop_constraint("uq_eta_submission_uuid", "egyptian_einvoice_documents", type_="unique")
    op.drop_constraint("uq_eta_source_document", "egyptian_einvoice_documents", type_="unique")
