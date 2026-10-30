"""Enforce globally unique, case-insensitive user login identifiers.

The migration intentionally refuses to delete or rewrite existing accounts.
Resolve any reported duplicate identities explicitly before retrying.
"""
from alembic import op
import sqlalchemy as sa


revision = "20261107_global_user_identity_uniqueness"
down_revision = "20261106_merge_inventory_approval_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    # This migration must never rely on potentially inconsistent indexes when
    # checking the physical user rows. Keep all preflight reads heap-based and
    # stop before any DDL if the primary key itself is duplicated.
    connection.exec_driver_sql("SET LOCAL enable_indexscan = off")
    connection.exec_driver_sql("SET LOCAL enable_indexonlyscan = off")
    connection.exec_driver_sql("SET LOCAL enable_bitmapscan = off")

    duplicate_primary_keys = connection.execute(sa.text("""
        SELECT id, array_agg(ctid::text ORDER BY ctid) AS physical_tuples,
               count(*) AS row_count
        FROM users
        GROUP BY id
        HAVING count(*) > 1
        ORDER BY id
    """)).mappings().all()

    duplicate_usernames = connection.execute(sa.text("""
        SELECT lower(trim(username)) AS normalized, array_agg(id ORDER BY id) AS user_ids
        FROM users
        GROUP BY lower(trim(username))
        HAVING count(*) > 1
        ORDER BY normalized
    """)).mappings().all()
    duplicate_emails = connection.execute(sa.text("""
        SELECT lower(trim(email)) AS normalized, array_agg(id ORDER BY id) AS user_ids
        FROM users
        GROUP BY lower(trim(email))
        HAVING count(*) > 1
        ORDER BY normalized
    """)).mappings().all()

    if duplicate_primary_keys or duplicate_usernames or duplicate_emails:
        details = []
        if duplicate_primary_keys:
            details.append("duplicate primary keys: " + "; ".join(
                f"user ID {row['id']} at physical tuples {row['physical_tuples']}"
                for row in duplicate_primary_keys
            ))
        if duplicate_usernames:
            details.append("duplicate usernames: " + "; ".join(
                f"{row['normalized']} (user IDs {row['user_ids']})" for row in duplicate_usernames
            ))
        if duplicate_emails:
            details.append("duplicate emails: " + "; ".join(
                f"{row['normalized']} (user IDs {row['user_ids']})" for row in duplicate_emails
            ))
        raise RuntimeError(
            "Global user identity uniqueness migration stopped without changing data. "
            + "Resolve these duplicates explicitly, then retry. "
            + " | ".join(details)
        )

    op.drop_constraint("uq_users_tenant_username", "users", type_="unique")
    op.drop_constraint("uq_users_tenant_email", "users", type_="unique")
    op.create_index(
        "uq_users_username_global_ci", "users",
        [sa.text("lower(trim(username))")], unique=True,
    )
    op.create_index(
        "uq_users_email_global_ci", "users",
        [sa.text("lower(trim(email))")], unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_users_email_global_ci", table_name="users")
    op.drop_index("uq_users_username_global_ci", table_name="users")
    op.create_unique_constraint(
        "uq_users_tenant_email", "users", ["tenant_id", "email"]
    )
    op.create_unique_constraint(
        "uq_users_tenant_username", "users", ["tenant_id", "username"]
    )
