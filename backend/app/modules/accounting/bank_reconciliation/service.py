from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.accounting.bank_reconciliation.models import BankAccount, BankStatementLine
from app.modules.treasury.models import TreasuryPayment

class BankReconciliationService:
    def list_accounts(self, db: Session, company_id: int):
        return list(db.scalars(select(BankAccount).where(BankAccount.company_id == company_id).order_by(BankAccount.id)).all())
    def create_account(self, db: Session, payload):
        if db.scalar(select(BankAccount).where(BankAccount.company_id == payload.company_id, BankAccount.code == payload.code.strip())):
            raise ValueError("Bank account code already exists")
        account = BankAccount(company_id=payload.company_id, code=payload.code.strip(), name=payload.name.strip(), currency_code=payload.currency_code.upper(), opening_balance=payload.opening_balance, is_active=1)
        db.add(account); db.flush(); return account
    def list_lines(self, db: Session, company_id: int, status: str | None = None):
        stmt = select(BankStatementLine).where(BankStatementLine.company_id == company_id)
        if status: stmt = stmt.where(BankStatementLine.status == status)
        return list(db.scalars(stmt.order_by(BankStatementLine.statement_date.desc(), BankStatementLine.id.desc())).all())
    def import_line(self, db: Session, payload):
        account = db.scalar(select(BankAccount).where(BankAccount.id == payload.bank_account_id, BankAccount.company_id == payload.company_id, BankAccount.is_active == 1))
        if account is None: raise ValueError("Bank account not found for this company")
        if payload.direction not in {"credit", "debit"}: raise ValueError("Direction must be credit or debit")
        line = BankStatementLine(**payload.model_dump(), status="unmatched")
        db.add(line); db.flush(); return line
    def match_payment(self, db: Session, company_id: int, line_id: int, payment_id: int):
        line = db.scalar(select(BankStatementLine).where(BankStatementLine.id == line_id, BankStatementLine.company_id == company_id).with_for_update())
        payment = db.scalar(select(TreasuryPayment).where(TreasuryPayment.id == payment_id, TreasuryPayment.company_id == company_id).with_for_update())
        if line is None or payment is None: raise ValueError("Statement line or payment not found")
        if line.status == "matched": raise ValueError("Statement line is already matched")
        if payment.status != "posted": raise ValueError("Only posted payments can be reconciled")
        expected_direction = "credit" if payment.direction == "receipt" else "debit"
        if line.direction != expected_direction or line.amount != payment.amount: raise ValueError("Statement line does not match payment amount/direction")
        line.status = "matched"; line.matched_payment_id = payment.id
        db.flush(); return line

bank_reconciliation_service = BankReconciliationService()
