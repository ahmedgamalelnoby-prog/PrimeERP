"""Add Helpdesk, Project execution, and Documents application foundations.

This is a domain foundation migration: it creates tenant/company-scoped
records and lifecycle primitives that the API/application layer can build on.
It intentionally avoids coupling to optional customer/user tables so the
migration remains safe across existing deployments.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260917_application_services_core"
down_revision = "20260917_tenant_module_sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "helpdesk_teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "code", name="uq_helpdesk_team_company_code"),
    )
    op.create_table(
        "helpdesk_stages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("folded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["team_id"], ["helpdesk_teams.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("team_id", "name", name="uq_helpdesk_stage_team_name"),
    )
    op.create_table(
        "helpdesk_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("ticket_no", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("customer_ref", sa.String(120)),
        sa.Column("assignee_ref", sa.String(120)),
        sa.Column("sla_due_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["helpdesk_teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["stage_id"], ["helpdesk_stages.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "ticket_no", name="uq_helpdesk_ticket_company_no"),
    )

    op.create_table(
        "project_milestones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("due_date", sa.Date()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "name", name="uq_project_milestone_name"),
    )
    op.create_table(
        "project_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("parent_task_id", sa.Integer()),
        sa.Column("milestone_id", sa.Integer()),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="todo"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("assignee_ref", sa.String(120)),
        sa.Column("customer_ref", sa.String(120)),
        sa.Column("planned_hours", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("deadline", sa.Date()),
        sa.Column("recurrence_rule", sa.String(160)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_task_id"], ["project_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["milestone_id"], ["project_milestones.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("project_id", "code", name="uq_project_task_code"),
    )
    op.create_table(
        "project_task_dependencies",
        sa.Column("predecessor_task_id", sa.Integer(), nullable=False),
        sa.Column("successor_task_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("predecessor_task_id", "successor_task_id"),
        sa.ForeignKeyConstraint(["predecessor_task_id"], ["project_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["successor_task_id"], ["project_tasks.id"], ondelete="CASCADE"),
        sa.CheckConstraint("predecessor_task_id <> successor_task_id", name="ck_project_task_dependency_not_self"),
    )

    op.create_table(
        "document_folders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer()),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("access_mode", sa.String(20), nullable=False, server_default="private"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["document_folders.id"], ondelete="SET NULL"),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("folder_id", sa.Integer()),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("document_type", sa.String(80), nullable=False, server_default="file"),
        sa.Column("external_key", sa.String(180)),
        sa.Column("storage_uri", sa.Text()),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("access_mode", sa.String(20), nullable=False, server_default="private"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("linked_model", sa.String(120)),
        sa.Column("linked_record_id", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["folder_id"], ["document_folders.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("company_id", "external_key", name="uq_document_company_external_key"),
    )
    op.create_table(
        "document_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(128)),
        sa.Column("created_by_ref", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("document_id", "version_no", name="uq_document_version"),
    )


def downgrade() -> None:
    for table in (
        "document_versions", "documents", "document_folders",
        "project_task_dependencies", "project_tasks", "project_milestones",
        "helpdesk_tickets", "helpdesk_stages", "helpdesk_teams",
    ):
        op.drop_table(table)
