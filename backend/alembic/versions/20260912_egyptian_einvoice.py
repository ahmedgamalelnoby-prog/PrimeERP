"""add Egyptian ETA e-invoice persistence and permissions

Revision ID: 20260912_egyptian_einvoice
Revises: 20260912_audit_events
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_egyptian_einvoice"
down_revision = "20260912_audit_events"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("einvoice.access", "einvoice", "access"),
    ("einvoice.write", "einvoice", "write"),
    ("einvoice.post", "einvoice", "post"),
)


def upgrade():
    op.create_table(
        "egyptian_einvoice_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=40), nullable=False),
        sa.Column("internal_number", sa.String(length=100), nullable=False),
        sa.Column("submission_uuid", sa.String(length=100), nullable=True),
        sa.Column("eta_uuid", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("payload_format", sa.String(length=20), nullable=False, server_default="json"),
        sa.Column("signed_payload", sa.Text(), nullable=True),
        sa.Column("eta_response", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("company_id", "source_type", "source_id", "document_type", name="uq_eta_company_source_document"),
        sa.CheckConstraint("status IN ('draft','queued','submitted','valid','rejected','cancelled','error')", name="ck_eta_document_status"),
        sa.CheckConstraint("payload_format IN ('json','xml')", name="ck_eta_document_payload_format"),
        sa.CheckConstraint("retry_count >= 0", name="ck_eta_document_retry_count"),
    )
    op.create_index("ix_eta_documents_company_id", "egyptian_einvoice_documents", ["company_id"])
    op.create_index("ix_eta_documents_source_id", "egyptian_einvoice_documents", ["source_id"])
    op.create_index("ix_eta_documents_submission_uuid", "egyptian_einvoice_documents", ["submission_uuid"])
    op.create_index("ix_eta_documents_eta_uuid", "egyptian_einvoice_documents", ["eta_uuid"])
    op.create_index("ix_eta_documents_status", "egyptian_einvoice_documents", ["status"])

    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("resource", sa.String),
        sa.column("action", sa.String),
        sa.column("description", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    for name, resource, action in PERMISSIONS:
        if op.get_bind().execute(sa.select(permissions.c.id).where(permissions.c.name == name)).first() is None:
            op.get_bind().execute(permissions.insert().values(name=name, resource=resource, action=action, description=f"{action.title()} Egyptian ETA e-invoice documents", is_active=True))


def downgrade():
    bind = op.get_bind()
    permissions = sa.table("permissions", sa.column("id", sa.Integer), sa.column("name", sa.String))
    ids = [row[0] for row in bind.execute(sa.select(permissions.c.id).where(permissions.c.name.in_([p[0] for p in PERMISSIONS]))).all()]
    if ids:
        role_permissions = sa.table("role_permissions", sa.column("permission_id", sa.Integer))
        bind.execute(role_permissions.delete().where(role_permissions.c.permission_id.in_(ids)))
        bind.execute(permissions.delete().where(permissions.c.id.in_(ids)))
    for name in ("ix_eta_documents_status", "ix_eta_documents_eta_uuid", "ix_eta_documents_submission_uuid", "ix_eta_documents_source_id", "ix_eta_documents_company_id"):
        op.drop_index(name, table_name="egyptian_einvoice_documents")
    op.drop_table("egyptian_einvoice_documents")
