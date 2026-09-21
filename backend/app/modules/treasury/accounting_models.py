from sqlalchemy import Boolean, Column, ForeignKey, Integer
from app.database.base import Base


class TreasuryAccountingSettings(Base):
    __tablename__ = "treasury_accounting_settings"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    journal_id = Column(Integer, ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=False)
    default_branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False)
    received_cheques_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    under_collection_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    returned_cheques_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    issued_cheques_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    bank_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False)
    auto_post = Column(Boolean, nullable=False, default=True)
