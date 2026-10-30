"""Enforce globally unique, case-insensitive user login identifiers.

Existing accounts are never deleted or rewritten. Duplicate normalized identifiers
stop the migration with the affected user IDs so they can be resolved explicitly.
"""
from alembic import op
import sqlalchemy as sa


revision = "20261107_global_user_identity_uniqueness"
down_revision = "20261106_merge_inventory_approval_heads"
branch_labels = None
depends_on = None


USERNAME_INDEX = "uq_users_username_global_ci"
EMAIL_INDEX = "uq_users_email_global_ci"
TENANT_USERNAME_CONSTRAINT = "uq_users_tenant_username"
TENANT_EMAIL_CONSTRAINT = "uq_users_tenant_email"


def _users_schema():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        raise RuntimeError("Cannot enforce user identity uniqueness: users table is missing.")
    constraints = {
        item.get("name")
        for item in inspector.get_unique_constraints("users")
        if item.get("name")
    }
    indexes = {
        item.get("name"): item
        for item in inspector.get_indexes("users")
        if item.get("name")
    }
    return constraints, indexes


def upgrade() -> None:
    bind = op.get_bind()
    constraints, indexes = _users_schema()

    duplicate_usernames = bind.execute(sa.text("""
        SELECT lower(trim(username)) AS normalized,
               array_agg(id ORDER BY id) AS user_ids
        FROM users
        GROUP BY lower(trim(username))
        HAVING count(*) > 1
        ORDER BY normalized
    """)).mappings().all()
    duplicate_emails = bind.execute(sa.text("""
        SELECT lower(trim(email)) AS normalized,
               array_agg(id ORDER BY id) AS user_ids
        FROM users
        GROUP BY lower(trim(email))
        HAVING count(*) > 1
        ORDER BY normalized
    """)).mappings().all()

    if duplicate_usernames or duplicate_emails:
        details = []
        if duplicate_usernames:
            details.append("duplicate usernames: " + "; ".join(
                f"{row['normalized']} (user IDs {row['user_ids']})"
                for row in duplicate_usernames
            ))
        if duplicate_emails:
            details.append("duplicate emails: " + "; ".join(
                f"{row['normalized']} (user IDs {row['user_ids']})"
                for row in duplicate_emails
            ))
        raise RuntimeError(
            "Global user identity uniqueness migration stopped without changing data. "
            "Resolve the reported duplicates explicitly, then retry. "
            + " | ".join(details)
        )

    # Older installations may not have both tenant-scoped constraints. Only
    # remove constraints that are actually present; never assume schema parity.
    if TENANT_USERNAME_CONSTRAINT in constraints:
        op.drop_constraint(TENANT_USERNAME_CONSTRAINT, "users", type_="unique")
    if TENANT_EMAIL_CONSTRAINT in constraints:
        op.drop_constraint(TENANT_EMAIL_CONSTRAINT, "users", type_="unique")

    if USERNAME_INDEX not in indexes:
        op.create_index(
            USERNAME_INDEX,
            "users",
            [sa.text("lower(trim(username))")],
            unique=True,
        )
    elif not indexes[USERNAME_INDEX].get("unique", False):
        raise RuntimeError(
            f"Cannot enforce global username uniqueness: index {USERNAME_INDEX} "
            "already exists but is not unique."
        )

    if EMAIL_INDEX not in indexes:
        op.create_index(
            EMAIL_INDEX,
            "users",
            [sa.text("lower(trim(email))")],
            unique=True,
        )
    elif not indexes[EMAIL_INDEX].get("unique", False):
        raise RuntimeError(
            f"Cannot enforce global email uniqueness: index {EMAIL_INDEX} "
            "already exists but is not unique."
        )


def downgrade() -> None:
    _, indexes = _users_schema()

    if EMAIL_INDEX in indexes:
        op.drop_index(EMAIL_INDEX, table_name="users")
    if USERNAME_INDEX in indexes:
        op.drop_index(USERNAME_INDEX, table_name="users")

    constraints, _ = _users_schema()
    if TENANT_EMAIL_CONSTRAINT not in constraints:
        op.create_unique_constraint(
            TENANT_EMAIL_CONSTRAINT, "users", ["tenant_id", "email"]
        )
    if TENANT_USERNAME_CONSTRAINT not in constraints:
        op.create_unique_constraint(
            TENANT_USERNAME_CONSTRAINT, "users", ["tenant_id", "username"]
        )
