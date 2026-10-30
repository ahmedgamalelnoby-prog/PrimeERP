from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_user_branch_membership_model_is_tenant_scoped_and_unique():
    model = source("app/modules/branches/models.py")
    block = model.split("class UserBranchMembership", 1)[1]
    assert '__tablename__ = "user_branch_memberships"' in block
    assert 'ForeignKey("tenants.id", ondelete="CASCADE")' in block
    assert 'ForeignKey("users.id", ondelete="CASCADE")' in block
    assert 'ForeignKey("branches.id", ondelete="CASCADE")' in block
    assert '"tenant_id",\n            "user_id",\n            "branch_id"' in block


def test_membership_model_is_registered_for_alembic_metadata():
    registry = source("app/database/models.py")
    assert "from app.modules.branches.models import Branch, UserBranchMembership" in registry
    assert "'Branch','UserBranchMembership','User'" in registry


def test_branch_membership_migration_is_chained_after_current_merge_head():
    migration = source("alembic/versions/20261107_user_branch_memberships.py")
    assert 'revision = "20261107_user_branch_memberships"' in migration
    assert 'down_revision = "20261106_merge_inventory_approval_heads"' in migration
    assert "op.create_table(" in migration
    assert '"user_branch_memberships"' in migration
    assert "uq_user_branch_memberships_tenant_user_branch" in migration


def test_branch_reads_are_limited_to_membership_unless_explicit_global_permission():
    router = source("app/modules/branches/router.py")
    assert 'user_has_permission(user, "branch.manage_all", db)' in router
    assert "UserBranchMembership.user_id == user.id" in router
    assert "UserBranchMembership.is_active.is_(True)" in router
    assert "UserBranchMembership.user_id == current_user.id" in router
    assert 'detail="You are not assigned to this branch"' in router


def test_branch_creation_and_creator_membership_are_committed_atomically():
    router = source("app/modules/branches/router.py")
    create = router.split("def create_branch(", 1)[1].split("@router.patch", 1)[0]
    assert "db.flush()" in create
    assert "UserBranchMembership(" in create
    assert "user_id=current_user.id" in create
    assert "assigned_by_user_id=current_user.id" in create
    assert create.index("db.add(branch)") < create.index("db.flush()")
    assert create.index("db.flush()") < create.index("UserBranchMembership(") < create.index("db.commit()")


def test_branch_members_can_only_be_assigned_from_the_same_tenant():
    router = source("app/modules/branches/router.py")
    assign = router.split("def assign_branch_member(", 1)[1].split("@router.delete", 1)[0]
    assert "User.tenant_id == branch.tenant_id" in assign
    assert "User.is_deleted.is_(False)" in assign
    assert "User.is_active.is_(True)" in assign
    assert "UserBranchMembership.tenant_id == branch.tenant_id" in assign


def test_branch_membership_can_be_revoked_without_deleting_audit_history():
    router = source("app/modules/branches/router.py")
    revoke = router.split("def revoke_branch_member(", 1)[1]
    assert "UserBranchMembership.is_active.is_(True)" in revoke
    assert "membership.is_active = False" in revoke
    assert "db.delete(" not in revoke


def test_branch_update_payload_cannot_change_tenant_or_company():
    schema = source("app/modules/branches/schemas.py")
    update = schema.split("class BranchUpdate", 1)[1].split("class BranchResponse", 1)[0]
    assert "tenant_id" not in update
    assert "company_id" not in update
