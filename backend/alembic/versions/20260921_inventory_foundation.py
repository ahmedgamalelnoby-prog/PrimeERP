"""inventory foundation: warehouses, locations, balances, movements, transfers, reservations and issues
Revision ID: 20260921_inventory_foundation
Revises: 20260921_master_data
"""
from alembic import op
import sqlalchemy as sa
revision="20260921_inventory_foundation"
down_revision="20260921_master_data"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("warehouses",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),nullable=False),
        sa.Column("branch_id",sa.Integer(),nullable=False),
        sa.Column("code",sa.String(50),nullable=False),
        sa.Column("name",sa.String(150),nullable=False),
        sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),
        sa.Column("updated_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"],["branches.id"],ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id","code",name="uq_warehouses_tenant_code"))
    for i,cols in [("ix_warehouses_id",["id"]),("ix_warehouses_tenant_id",["tenant_id"]),("ix_warehouses_branch_id",["branch_id"]),("ix_warehouses_is_active",["is_active"])]:
        op.create_index(i,"warehouses",cols)

    op.create_table("warehouse_locations",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),nullable=False),
        sa.Column("warehouse_id",sa.Integer(),nullable=False),
        sa.Column("parent_id",sa.Integer(),nullable=True),
        sa.Column("code",sa.String(50),nullable=False),
        sa.Column("name",sa.String(150),nullable=False),
        sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"],["warehouses.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"],["warehouse_locations.id"],ondelete="CASCADE"),
        sa.UniqueConstraint("warehouse_id","code",name="uq_warehouse_locations_warehouse_code"))
    for i,cols in [("ix_warehouse_locations_id",["id"]),("ix_warehouse_locations_tenant_id",["tenant_id"]),("ix_warehouse_locations_warehouse_id",["warehouse_id"]),("ix_warehouse_locations_parent_id",["parent_id"]),("ix_warehouse_locations_is_active",["is_active"])]:
        op.create_index(i,"warehouse_locations",cols)

    op.create_table("stock_balances",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),nullable=False),
        sa.Column("warehouse_id",sa.Integer(),nullable=False),
        sa.Column("location_id",sa.Integer(),nullable=False),
        sa.Column("product_id",sa.Integer(),nullable=False),
        sa.Column("quantity",sa.Numeric(18,6),nullable=False,server_default="0"),
        sa.Column("reserved_quantity",sa.Numeric(18,6),nullable=False,server_default="0"),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"],["warehouses.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"],["warehouse_locations.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"],["products.id"],ondelete="RESTRICT"),
        sa.UniqueConstraint("tenant_id","location_id","product_id",name="uq_stock_balances_location_product"),
        sa.CheckConstraint("quantity >= 0",name="ck_stock_balances_quantity_nonnegative"),
        sa.CheckConstraint("reserved_quantity >= 0 AND reserved_quantity <= quantity",name="ck_stock_balances_reserved_valid"))
    for i,cols in [("ix_stock_balances_id",["id"]),("ix_stock_balances_tenant_id",["tenant_id"]),("ix_stock_balances_warehouse_id",["warehouse_id"]),("ix_stock_balances_location_id",["location_id"]),("ix_stock_balances_product_id",["product_id"])]:
        op.create_index(i,"stock_balances",cols)

    op.create_table("stock_movements",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),nullable=False),
        sa.Column("product_id",sa.Integer(),nullable=False),
        sa.Column("warehouse_id",sa.Integer(),nullable=False),
        sa.Column("location_id",sa.Integer(),nullable=False),
        sa.Column("movement_type",sa.String(30),nullable=False),
        sa.Column("quantity",sa.Numeric(18,6),nullable=False),
        sa.Column("reference_type",sa.String(50)),
        sa.Column("reference_id",sa.Integer()),
        sa.Column("notes",sa.Text()),
        sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"],["products.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"],["warehouses.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"],["warehouse_locations.id"],ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0",name="ck_stock_movements_quantity_positive"))
    for i,cols in [("ix_stock_movements_id",["id"]),("ix_stock_movements_tenant_id",["tenant_id"]),("ix_stock_movements_product_id",["product_id"]),("ix_stock_movements_warehouse_id",["warehouse_id"]),("ix_stock_movements_location_id",["location_id"]),("ix_stock_movements_movement_type",["movement_type"]),("ix_stock_movements_reference_type",["reference_type"]),("ix_stock_movements_reference_id",["reference_id"])]:
        op.create_index(i,"stock_movements",cols)

    op.create_table("stock_transfers",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),nullable=False),
        sa.Column("source_warehouse_id",sa.Integer(),nullable=False),
        sa.Column("destination_warehouse_id",sa.Integer(),nullable=False),
        sa.Column("status",sa.String(30),nullable=False,server_default="posted"),
        sa.Column("notes",sa.Text()),
        sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_warehouse_id"],["warehouses.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destination_warehouse_id"],["warehouses.id"],ondelete="RESTRICT"))
    for i,cols in [("ix_stock_transfers_id",["id"]),("ix_stock_transfers_tenant_id",["tenant_id"]),("ix_stock_transfers_source_warehouse_id",["source_warehouse_id"]),("ix_stock_transfers_destination_warehouse_id",["destination_warehouse_id"]),("ix_stock_transfers_status",["status"])]:
        op.create_index(i,"stock_transfers",cols)

    op.create_table("stock_transfer_lines",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("transfer_id",sa.Integer(),nullable=False),
        sa.Column("product_id",sa.Integer(),nullable=False),
        sa.Column("source_location_id",sa.Integer(),nullable=False),
        sa.Column("destination_location_id",sa.Integer(),nullable=False),
        sa.Column("quantity",sa.Numeric(18,6),nullable=False),
        sa.ForeignKeyConstraint(["transfer_id"],["stock_transfers.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"],["products.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_location_id"],["warehouse_locations.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destination_location_id"],["warehouse_locations.id"],ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0",name="ck_stock_transfer_lines_quantity_positive"))
    for i,cols in [("ix_stock_transfer_lines_id",["id"]),("ix_stock_transfer_lines_transfer_id",["transfer_id"]),("ix_stock_transfer_lines_product_id",["product_id"]),("ix_stock_transfer_lines_source_location_id",["source_location_id"]),("ix_stock_transfer_lines_destination_location_id",["destination_location_id"])]:
        op.create_index(i,"stock_transfer_lines",cols)

    op.create_table("stock_reservations",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),nullable=False),
        sa.Column("reference_type",sa.String(50),nullable=False),
        sa.Column("reference_id",sa.Integer(),nullable=False),
        sa.Column("status",sa.String(30),nullable=False,server_default="reserved"),
        sa.Column("notes",sa.Text()),
        sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"))
    for i,cols in [("ix_stock_reservations_id",["id"]),("ix_stock_reservations_tenant_id",["tenant_id"]),("ix_stock_reservations_reference_type",["reference_type"]),("ix_stock_reservations_reference_id",["reference_id"]),("ix_stock_reservations_status",["status"])]:
        op.create_index(i,"stock_reservations",cols)

    op.create_table("stock_reservation_lines",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("reservation_id",sa.Integer(),nullable=False),
        sa.Column("product_id",sa.Integer(),nullable=False),
        sa.Column("location_id",sa.Integer(),nullable=False),
        sa.Column("quantity",sa.Numeric(18,6),nullable=False),
        sa.ForeignKeyConstraint(["reservation_id"],["stock_reservations.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"],["products.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"],["warehouse_locations.id"],ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0",name="ck_stock_reservation_lines_quantity_positive"))
    for i,cols in [("ix_stock_reservation_lines_id",["id"]),("ix_stock_reservation_lines_reservation_id",["reservation_id"]),("ix_stock_reservation_lines_product_id",["product_id"]),("ix_stock_reservation_lines_location_id",["location_id"])]:
        op.create_index(i,"stock_reservation_lines",cols)

    op.create_table("stock_issues",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),nullable=False),
        sa.Column("warehouse_id",sa.Integer(),nullable=False),
        sa.Column("issue_type",sa.String(30),nullable=False,server_default="consumption"),
        sa.Column("reference_type",sa.String(50)),
        sa.Column("reference_id",sa.Integer()),
        sa.Column("status",sa.String(30),nullable=False,server_default="posted"),
        sa.Column("notes",sa.Text()),
        sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"],["warehouses.id"],ondelete="RESTRICT"))
    for i,cols in [("ix_stock_issues_id",["id"]),("ix_stock_issues_tenant_id",["tenant_id"]),("ix_stock_issues_warehouse_id",["warehouse_id"]),("ix_stock_issues_issue_type",["issue_type"]),("ix_stock_issues_reference_type",["reference_type"]),("ix_stock_issues_reference_id",["reference_id"]),("ix_stock_issues_status",["status"])]:
        op.create_index(i,"stock_issues",cols)

    op.create_table("stock_issue_lines",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("issue_id",sa.Integer(),nullable=False),
        sa.Column("product_id",sa.Integer(),nullable=False),
        sa.Column("location_id",sa.Integer(),nullable=False),
        sa.Column("quantity",sa.Numeric(18,6),nullable=False),
        sa.ForeignKeyConstraint(["issue_id"],["stock_issues.id"],ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"],["products.id"],ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"],["warehouse_locations.id"],ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0",name="ck_stock_issue_lines_quantity_positive"))
    for i,cols in [("ix_stock_issue_lines_id",["id"]),("ix_stock_issue_lines_issue_id",["issue_id"]),("ix_stock_issue_lines_product_id",["product_id"]),("ix_stock_issue_lines_location_id",["location_id"])]:
        op.create_index(i,"stock_issue_lines",cols)

def downgrade():
    for i,t in [
        ("ix_stock_issue_lines_location_id","stock_issue_lines"),("ix_stock_issue_lines_product_id","stock_issue_lines"),("ix_stock_issue_lines_issue_id","stock_issue_lines"),("ix_stock_issue_lines_id","stock_issue_lines")]: op.drop_index(i,table_name=t)
    op.drop_table("stock_issue_lines")
    for i,t in [("ix_stock_issues_status","stock_issues"),("ix_stock_issues_reference_id","stock_issues"),("ix_stock_issues_reference_type","stock_issues"),("ix_stock_issues_issue_type","stock_issues"),("ix_stock_issues_warehouse_id","stock_issues"),("ix_stock_issues_tenant_id","stock_issues"),("ix_stock_issues_id","stock_issues")]: op.drop_index(i,table_name=t)
    op.drop_table("stock_issues")
    for i,t in [("ix_stock_reservation_lines_location_id","stock_reservation_lines"),("ix_stock_reservation_lines_product_id","stock_reservation_lines"),("ix_stock_reservation_lines_reservation_id","stock_reservation_lines"),("ix_stock_reservation_lines_id","stock_reservation_lines")]: op.drop_index(i,table_name=t)
    op.drop_table("stock_reservation_lines")
    for i,t in [("ix_stock_reservations_status","stock_reservations"),("ix_stock_reservations_reference_id","stock_reservations"),("ix_stock_reservations_reference_type","stock_reservations"),("ix_stock_reservations_tenant_id","stock_reservations"),("ix_stock_reservations_id","stock_reservations")]: op.drop_index(i,table_name=t)
    op.drop_table("stock_reservations")
    for i,t in [("ix_stock_transfer_lines_destination_location_id","stock_transfer_lines"),("ix_stock_transfer_lines_source_location_id","stock_transfer_lines"),("ix_stock_transfer_lines_product_id","stock_transfer_lines"),("ix_stock_transfer_lines_transfer_id","stock_transfer_lines"),("ix_stock_transfer_lines_id","stock_transfer_lines")]: op.drop_index(i,table_name=t)
    op.drop_table("stock_transfer_lines")
    for i,t in [("ix_stock_transfers_status","stock_transfers"),("ix_stock_transfers_destination_warehouse_id","stock_transfers"),("ix_stock_transfers_source_warehouse_id","stock_transfers"),("ix_stock_transfers_tenant_id","stock_transfers"),("ix_stock_transfers_id","stock_transfers")]: op.drop_index(i,table_name=t)
    op.drop_table("stock_transfers")
    for i,t in [("ix_stock_movements_reference_id","stock_movements"),("ix_stock_movements_reference_type","stock_movements"),("ix_stock_movements_movement_type","stock_movements"),("ix_stock_movements_location_id","stock_movements"),("ix_stock_movements_warehouse_id","stock_movements"),("ix_stock_movements_product_id","stock_movements"),("ix_stock_movements_tenant_id","stock_movements"),("ix_stock_movements_id","stock_movements")]: op.drop_index(i,table_name=t)
    op.drop_table("stock_movements")
    for i,t in [("ix_stock_balances_product_id","stock_balances"),("ix_stock_balances_location_id","stock_balances"),("ix_stock_balances_warehouse_id","stock_balances"),("ix_stock_balances_tenant_id","stock_balances"),("ix_stock_balances_id","stock_balances")]: op.drop_index(i,table_name=t)
    op.drop_table("stock_balances")
    for i,t in [("ix_warehouse_locations_is_active","warehouse_locations"),("ix_warehouse_locations_parent_id","warehouse_locations"),("ix_warehouse_locations_warehouse_id","warehouse_locations"),("ix_warehouse_locations_tenant_id","warehouse_locations"),("ix_warehouse_locations_id","warehouse_locations")]: op.drop_index(i,table_name=t)
    op.drop_table("warehouse_locations")
    for i,t in [("ix_warehouses_is_active","warehouses"),("ix_warehouses_branch_id","warehouses"),("ix_warehouses_tenant_id","warehouses"),("ix_warehouses_id","warehouses")]: op.drop_index(i,table_name=t)
    op.drop_table("warehouses")
