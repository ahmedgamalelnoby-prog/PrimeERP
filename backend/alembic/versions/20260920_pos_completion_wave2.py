"""POS modifiers and promotions."""
from alembic import op
import sqlalchemy as sa
revision="20260920_pos_completion_wave2"
down_revision="20260920_completion_wave2"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("pos_modifier_groups",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("min_select",sa.Integer(),nullable=False,server_default="0"),sa.Column("max_select",sa.Integer(),nullable=False,server_default="1"),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()))
 op.create_table("pos_modifier_options",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("group_id",sa.Integer(),sa.ForeignKey("pos_modifier_groups.id",ondelete="CASCADE"),nullable=False),sa.Column("code",sa.String(60),nullable=False),sa.Column("name",sa.String(160),nullable=False),sa.Column("price_delta",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.UniqueConstraint("group_id","code",name="uq_pos_modifier_option"))
 op.create_table("pos_promotions",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("code",sa.String(80),nullable=False),sa.Column("name",sa.String(160),nullable=False),sa.Column("discount_percent",sa.Numeric(8,4),nullable=False,server_default="0"),sa.Column("min_subtotal",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("max_discount",sa.Numeric(18,4)),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("valid_from",sa.DateTime(timezone=True)),sa.Column("valid_to",sa.DateTime(timezone=True)),sa.UniqueConstraint("company_id","code",name="uq_pos_promotion_code"))
 op.create_table("pos_promotion_uses",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("promotion_id",sa.Integer(),sa.ForeignKey("pos_promotions.id",ondelete="RESTRICT"),nullable=False),sa.Column("sales_document_id",sa.Integer(),sa.ForeignKey("sales_documents.id",ondelete="RESTRICT"),nullable=False),sa.Column("discount_amount",sa.Numeric(18,4),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.UniqueConstraint("promotion_id","sales_document_id",name="uq_pos_promotion_use"))
def downgrade():
 for t in ["pos_promotion_uses","pos_promotions","pos_modifier_options","pos_modifier_groups"]:op.drop_table(t)
