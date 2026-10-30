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
    assert "branch.manage_all" in migration
    assert "ON CONFLICT (name) DO NOTHING" in migration


def test_branch_reads_are_limited_to_membership_unless_explicit_global_permission():
    router = source("app/modules/branches/router.py")
    manifest = source("app/modules/branches/__manifest__.py")
    assert "branch.manage_all" in manifest
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


def test_shared_branch_access_helper_checks_tenant_membership_and_active_branch():
    access = source("app/modules/branches/access.py")
    assert "Branch.tenant_id == tenant_id" in access
    assert "Branch.is_active.is_(True)" in access
    assert "UserBranchMembership.user_id == user.id" in access
    assert "UserBranchMembership.is_active.is_(True)" in access
    assert '"branch.manage_all"' in access


def test_warehouse_list_is_filtered_to_assigned_branches_for_regular_users():
    router = source("app/modules/inventory/warehouses/router.py")
    service = source("app/modules/inventory/warehouses/service.py")
    assert "require_branch_access(db, current_user, branch_id)" in router
    assert "accessible_branch_ids(db, current_user)" in router
    assert "allowed_branch_ids=allowed" in router
    assert "InventoryWarehouse.branch_id.in_(allowed_branch_ids)" in service


def test_central_warehouse_requires_tenant_wide_permission_for_creation_and_update():
    router = source("app/modules/inventory/warehouses/router.py")
    assert "Tenant-wide branch management permission is required for a central warehouse" in router
    assert "can_manage_all_branches(db, current_user)" in router


def test_warehouse_creation_validates_branch_company_and_user_membership():
    router = source("app/modules/inventory/warehouses/router.py")
    create = router.split("def create_warehouse(", 1)[1].split("@router.patch", 1)[0]
    assert "require_branch_access(db, current_user, payload.branch_id)" in create
    assert "branch.company_id != company.id" in create


def test_stock_move_create_post_and_reverse_validate_both_location_branches():
    router = source("app/modules/inventory/stock_moves/router.py")
    assert "def _authorize_stock_move_locations(" in router
    assert "for branch_id in branch_ids:" in router
    assert "require_branch_access(db, user, branch_id)" in router
    assert "_authorize_stock_move_locations(" in router
    assert "_authorize_existing_stock_move(db, user, company_id, move_id)" in router


def test_stock_move_list_excludes_unassigned_branch_endpoints():
    router = source("app/modules/inventory/stock_moves/router.py")
    assert "source_warehouse.branch_id.in_(allowed)" in router
    assert "destination_warehouse.branch_id.in_(allowed)" in router
    assert "or_(source_warehouse.branch_id.in_(allowed), destination_warehouse.branch_id.in_(allowed))" in router


def test_inventory_accounting_configuration_requires_branch_membership():
    router = source("app/modules/inventory/stock_moves/router.py")
    save = router.split("def save_accounting_config(", 1)[1].split("@router.post", 1)[0]
    assert "require_branch_access(db, user, payload.branch_id)" in save
    assert "branch.company_id != payload.company_id" in save
    read = router.split("def get_accounting_config(", 1)[1].split("@router.put", 1)[0]
    assert "require_branch_access(db, user, config.branch_id)" in read


def test_catalog_menu_reads_and_writes_respect_branch_membership():
    router = source("app/modules/catalog/router.py")
    assert "def _assert_menu_access(" in router
    assert "require_branch_access(db, user, menu.branch_id)" in router
    assert "Tenant-wide branch management permission is required for a company-wide menu" in router
    assert "menu.branch_id is None or menu.branch_id in company_branch_ids" in router
    assert "_assert_menu_access(db, current_user, company_id, menu)" in router


def test_commerce_accounting_settings_default_branch_is_membership_scoped():
    router = source("app/modules/commerce/router.py")
    assert "branch = require_branch_access(db, current_user, payload.default_branch_id)" in router
    assert "branch = require_branch_access(db, current_user, obj.default_branch_id)" in router


def test_shipping_carriers_and_shipments_are_branch_scoped():
    router = source("app/modules/shipping/router.py")
    assert "def _require_carrier_branch_access(" in router
    assert "require_branch_access(db, user, carrier_obj.branch_id)" in router
    assert "ShippingCarrier.branch_id.in_(allowed)" in router
    assert "_require_carrier_branch_access(db, current_user, carrier_obj)" in router
    assert "_require_carrier_branch_access(db, current_user, carrier_obj)" in router
