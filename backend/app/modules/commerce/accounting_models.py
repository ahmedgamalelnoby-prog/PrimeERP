from sqlalchemy import Boolean, Column, ForeignKey, Integer, UniqueConstraint
from app.database.base import Base


class CommerceAccountingSettings(Base):
    __tablename__ = "commerce_accounting_settings"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    sales_journal_id = Column(Integer, ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False)
    purchase_journal_id = Column(Integer, ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False)
    cash_journal_id = Column(Integer, ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False)
    ar_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    ap_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    sales_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    purchase_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    inventory_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    grni_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    purchase_price_variance_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=True)
    cogs_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    output_vat_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    input_vat_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    wht_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=True)
    default_payment_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    default_branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False)
    auto_post = Column(Boolean, nullable=False, default=True)

    __table_args__ = (UniqueConstraint("company_id", name="uq_commerce_accounting_settings_company"),)
