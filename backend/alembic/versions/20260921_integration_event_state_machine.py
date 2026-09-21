"""normalize and constrain integration event processing states.

Revision ID: 20260921_integration_event_state_machine
Revises: 20260916_release_graph_absolute_merge
"""

from alembic import op
import sqlalchemy as sa

revision = "20260921_integration_event_state_machine"
down_revision = "20260916_release_graph_absolute_merge"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            UPDATE integration_events
            SET status = 'queued'
            WHERE status IN ('failed', 'retry', 'retrying')
              AND COALESCE(attempts, 0) < 10
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE integration_events
            SET status = 'dead_letter', next_attempt_at = NULL
            WHERE status IN ('failed', 'retry', 'retrying')
              AND COALESCE(attempts, 0) >= 10
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE integration_events
            SET status = 'queued'
            WHERE status = 'processing'
              AND COALESCE(attempts, 0) < 10
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE integration_events
            SET status = 'dead_letter', next_attempt_at = NULL
            WHERE status = 'processing'
              AND COALESCE(attempts, 0) >= 10
            """
        )
    )

    invalid = bind.execute(
        sa.text(
            """
            SELECT id, status
            FROM integration_events
            WHERE status NOT IN ('received', 'queued', 'processing', 'processed', 'dead_letter')
            """
        )
    ).fetchall()
    if invalid:
        raise RuntimeError(
            "Cannot normalize integration_events with unknown statuses: "
            + ", ".join(f"{row[0]}={row[1]!r}" for row in invalid)
        )

    op.create_check_constraint(
        "ck_integration_events_status",
        "integration_events",
        "status IN ('received','queued','processing','processed','dead_letter')",
    )
    op.create_index(
        "ix_integration_events_processing_due",
        "integration_events",
        ["status", "next_attempt_at", "id"],
    )


def downgrade():
    op.drop_index("ix_integration_events_processing_due", table_name="integration_events")
    op.drop_constraint("ck_integration_events_status", "integration_events", type_="check")
