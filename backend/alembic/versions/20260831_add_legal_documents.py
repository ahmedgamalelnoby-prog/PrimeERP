"""add editable legal documents and acceptance tracking

Revision ID: 20260831legal
Revises: 23a89dc7f2a4
Create Date: 2026-08-31

The previous merge listed 3e705e622f62 together with its descendant
23a89dc7f2a4. Keeping the descendant alone preserves the complete lineage
without declaring an ancestor and descendant as parallel merge parents.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260831legal"
down_revision: Union[str, Sequence[str], None] = "23a89dc7f2a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "legal_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_type", sa.String(length=30), nullable=False),
        sa.Column("title_ar", sa.String(length=200), nullable=False),
        sa.Column("title_en", sa.String(length=200), nullable=False),
        sa.Column("content_ar", sa.Text(), nullable=False),
        sa.Column("content_en", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("document_type", name="uq_legal_document_type"),
    )
    op.create_index("ix_legal_documents_document_type", "legal_documents", ["document_type"], unique=False)
    op.create_index("ix_legal_documents_is_published", "legal_documents", ["is_published"], unique=False)

    op.create_table(
        "legal_acceptances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=30), nullable=False),
        sa.Column("document_version", sa.Integer(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "document_type", "document_version", name="uq_legal_acceptance"),
    )
    op.create_index("ix_legal_acceptances_user_id", "legal_acceptances", ["user_id"], unique=False)
    op.create_index("ix_legal_acceptances_document_type", "legal_acceptances", ["document_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_legal_acceptances_document_type", table_name="legal_acceptances")
    op.drop_index("ix_legal_acceptances_user_id", table_name="legal_acceptances")
    op.drop_table("legal_acceptances")
    op.drop_index("ix_legal_documents_is_published", table_name="legal_documents")
    op.drop_index("ix_legal_documents_document_type", table_name="legal_documents")
    op.drop_table("legal_documents")
