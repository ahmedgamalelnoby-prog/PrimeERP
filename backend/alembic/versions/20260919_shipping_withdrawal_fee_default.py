"""add carrier withdrawal fee to the canonical delivered status

Revision ID: 20260919_shipping_withdrawal_fee_default
Revises: 20260919_shipping_status_custom_codes
"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_shipping_withdrawal_fee_default"
down_revision = "20260919_shipping_status_custom_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("""
        SELECT id, financial_actions
        FROM shipping_order_statuses
        WHERE code = 'delivered'
    """)).mappings().all()
    for row in rows:
        actions = []
        raw = row["financial_actions"]
        if raw:
            import json
            actions = json.loads(raw)
        if "recognize_payment_withdrawal_fee" not in actions:
            actions.append("recognize_payment_withdrawal_fee")
            conn.execute(
                sa.text("""
                    UPDATE shipping_order_statuses
                    SET financial_actions = :actions
                    WHERE id = :id
                """),
                {"id": row["id"], "actions": json.dumps(actions)},
            )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("""
        SELECT id, financial_actions
        FROM shipping_order_statuses
        WHERE code = 'delivered'
    """)).mappings().all()
    import json
    for row in rows:
        actions = json.loads(row["financial_actions"] or "[]")
        actions = [x for x in actions if x != "recognize_payment_withdrawal_fee"]
        conn.execute(
            sa.text("""
                UPDATE shipping_order_statuses
                SET financial_actions = :actions
                WHERE id = :id
            """),
            {"id": row["id"], "actions": json.dumps(actions)},
        )
