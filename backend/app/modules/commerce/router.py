from app.core.context.access import require_company_access, require_branch_access
from app.core.context import get_optional_request_context
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.accounting.journals.models import AccountingJournal
from app.modules.branches.models import Branch
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.commerce.accounting_schemas import CommerceAccountingSettingsCreate
from app.modules.commerce.models import CommercePayment, SalesDocument, PurchaseDocument
from app.modules.commerce.schemas import PartnerCreate, PartnerResponse, DocumentCreate, DocumentResponse, PaymentCreate, PaymentResponse, PaymentReverse, AgingSummary, PartnerStatement, CommerceApprovalDecision
from app.modules.commerce.sales_return_schemas import SalesReturnCreate
from app.modules.commerce.sales_return_service import sales_return_service
from app.modules.commerce.service import commerce_service
from app.modules.companies.models import Company
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.jurisdiction.commerce_guard import capture_document_tax_snapshot, validate_document_tax_snapshot

router = APIRouter(prefix="/commerce", tags=["Commerce"], dependencies=[Depends(require_permission("commerce.access"))])


def _company_for_user(db: Session, company_id: int, user: User):
    return require_company_access(db, company_id, user)
def _report_branch_id(db: Session, company_id: int, user: User) -> int | None:
    if user.is_platform_admin:
        return None
    context = get_optional_request_context()
    if context is None or context.branch_id is None:
        raise HTTPException(400, "Select a branch using X-Branch-ID before viewing branch financial reports")
    require_branch_access(db, company_id, context.branch_id, user)
    return context.branch_id


def _assert_warehouse_access(db: Session, company_id: int, warehouse_id: int | None, user: User) -> None:
    if warehouse_id is None:
        return
    warehouse = db.scalar(select(InventoryWarehouse).where(
        InventoryWarehouse.id == warehouse_id,
        InventoryWarehouse.company_id == company_id,
        InventoryWarehouse.is_active.is_(True),
    ))
    if warehouse is None:
        raise HTTPException(404, "Warehouse not found for this company")
    if warehouse.branch_id is not None:
        require_branch_access(db, company_id, warehouse.branch_id, user)


def _assert_document_access(db: Session, company_id: int, document_id: int, kind: str, user: User):
    model = SalesDocument if kind == "sale" else PurchaseDocument
    document = db.scalar(select(model).where(model.id == document_id, model.company_id == company_id))
    if document is None:
        raise HTTPException(404, "Document not found")
    _assert_warehouse_access(db, company_id, document.warehouse_id, user)
    return document


def _list_documents_for_user(db: Session, company_id: int, kind: str, document_type: str | None, user: User):
    model = SalesDocument if kind == "sale" else PurchaseDocument
    query = select(model).where(model.company_id == company_id)
    if document_type is not None:
        query = query.where(model.document_type == document_type)
    if not user.is_platform_admin:
        context = get_optional_request_context()
        if context is None or context.branch_id is None:
            raise HTTPException(400, "Select a branch using X-Branch-ID before listing branch documents")
        require_branch_access(db, company_id, context.branch_id, user)
        query = query.outerjoin(InventoryWarehouse, InventoryWarehouse.id == model.warehouse_id).where(
            or_(
                model.warehouse_id.is_(None),
                InventoryWarehouse.is_central.is_(True),
                InventoryWarehouse.branch_id == context.branch_id,
            )
        )
    return list(db.scalars(query.order_by(model.document_date.desc(), model.id.desc())).all())


def _run(fn):
    try:
        return fn()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="The request conflicts with an existing record") from exc


def _validate_accounting_configuration(db: Session, company: Company, payload: CommerceAccountingSettingsCreate) -> None:
    journal_ids = {
        "sales journal": payload.sales_journal_id,
        "purchase journal": payload.purchase_journal_id,
        "cash journal": payload.cash_journal_id,
    }
    journals = db.scalars(
        select(AccountingJournal).where(
            AccountingJournal.id.in_(journal_ids.values()),
            AccountingJournal.company_id == company.id,
            AccountingJournal.tenant_id == company.tenant_id,
            AccountingJournal.is_active.is_(True),
        )
    ).all()
    journal_by_id = {journal.id: journal for journal in journals}
    for label, journal_id in journal_ids.items():
        if journal_id not in journal_by_id:
            raise HTTPException(422, f"Configured {label} does not belong to this company/tenant or is inactive")
    account_ids = {
        "AR account": payload.ar_account_id,
        "AP account": payload.ap_account_id,
        "sales account": payload.sales_account_id,
        "purchase account": payload.purchase_account_id,
        "inventory account": payload.inventory_account_id,
        "GRNI account": payload.grni_account_id,
        "PPV account": payload.purchase_price_variance_account_id,
        "COGS account": payload.cogs_account_id,
        "output VAT account": payload.output_vat_account_id,
        "input VAT account": payload.input_vat_account_id,
        "default payment account": payload.default_payment_account_id,
    }
    if payload.wht_account_id is not None:
        account_ids["WHT account"] = payload.wht_account_id
    accounts = db.scalars(
        select(AccountCombination).where(
            AccountCombination.id.in_(account_ids.values()),
            AccountCombination.company_id == company.id,
            AccountCombination.is_active.is_(True),
        )
    ).all()
    account_by_id = {account.id: account for account in accounts}
    for label, account_id in account_ids.items():
        if account_id not in account_by_id:
            raise HTTPException(422, f"Configured {label} does not belong to this company or is inactive")


@router.post("/accounting-settings", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def configure_accounting(payload: CommerceAccountingSettingsCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = _company_for_user(db, payload.company_id, current_user)
    branch = db.scalar(select(Branch).where(Branch.id == payload.default_branch_id, Branch.company_id == company.id, Branch.tenant_id == company.tenant_id, Branch.is_active.is_(True)))
    if branch is None: raise HTTPException(422, "Default branch does not belong to the company")
    _validate_accounting_configuration(db, company, payload)
    values = payload.model_dump(); obj = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company.id))
    if obj is None: obj = CommerceAccountingSettings(**values); db.add(obj)
    else:
        for key, value in values.items(): setattr(obj, key, value)
    db.commit(); db.refresh(obj); return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name != "id"}


@router.get("/accounting-settings")
def get_accounting_settings(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); obj = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company_id))
    if obj is None: raise HTTPException(404, "Commerce accounting configuration not found")
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name != "id"}


@router.post("/partners", response_model=PartnerResponse, status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_partner(payload: PartnerCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user); obj = _run(lambda: commerce_service.create_partner(db, payload)); db.commit(); db.refresh(obj); return obj


@router.get("/partners", response_model=list[PartnerResponse])
def list_partners(company_id: int = Query(..., gt=0), partner_type: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return commerce_service.list_partners(db, company_id, partner_type)


@router.post("/sales/documents", response_model=DocumentResponse, status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_sale(payload: DocumentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    _assert_warehouse_access(db, payload.company_id, payload.warehouse_id, current_user)
    if payload.document_type not in {"quotation", "order", "delivery", "invoice", "credit_note"}: raise HTTPException(400, "Invalid sales document type")
    obj = _run(lambda: commerce_service.create_document(db, payload)); db.commit(); db.refresh(obj); return obj


@router.post("/sales/returns", response_model=DocumentResponse, status_code=201, dependencies=[Depends(require_permission("commerce.post"))])
def create_sales_return(payload: SalesReturnCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    try: obj = sales_return_service.create_and_post(db, payload, current_user.id); db.commit(); db.refresh(obj); return obj
    except ValueError as exc: db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="The sales return conflicts with an existing allocation or document") from exc


@router.post("/purchases/documents", response_model=DocumentResponse, status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_purchase(payload: DocumentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    _assert_warehouse_access(db, payload.company_id, payload.warehouse_id, current_user)
    if payload.document_type not in {"requisition", "rfq", "order", "receipt", "bill", "debit_note"}: raise HTTPException(400, "Invalid purchase document type")
    obj = _run(lambda: commerce_service.create_document(db, payload)); db.commit(); db.refresh(obj); return obj


@router.get("/ar-ap/aging", response_model=AgingSummary)
def ar_ap_aging(company_id: int = Query(..., gt=0), as_of: date | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    cutoff = as_of or date.today()
    branch_id = _report_branch_id(db, company_id, current_user)
    rows = commerce_service.ar_ap_aging(db, company_id, cutoff, branch_id=branch_id)
    receivable = sum((r["outstanding"] for r in rows if r["direction"] == "receivable"), 0)
    payable = sum((r["outstanding"] for r in rows if r["direction"] == "payable"), 0)
    return {"as_of": cutoff, "receivable": receivable, "payable": payable, "net": receivable - payable, "rows": rows}

@router.get("/partners/{partner_id}/statement", response_model=PartnerStatement)
def partner_statement(
    partner_id: int,
    company_id: int = Query(..., gt=0),
    direction: str = Query(..., pattern="^(customer|vendor)$"),
    from_date: date | None = None,
    to_date: date | None = None,
    as_of: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company_for_user(db, company_id, current_user)
    branch_id = _report_branch_id(db, company_id, current_user)
    if from_date and to_date and from_date > to_date:
        raise HTTPException(400, "from_date cannot be later than to_date")
    cutoff = as_of or to_date or date.today()
    result = _run(lambda: commerce_service.partner_statement(
        db, company_id, partner_id, direction, from_date, to_date, cutoff, branch_id=branch_id
    ))
    result.update({"company_id": company_id, "partner_id": partner_id, "direction": direction, "from_date": from_date, "to_date": to_date, "as_of": cutoff})
    return result


@router.get("/sales/documents", response_model=list[DocumentResponse])
def sales(
    company_id: int = Query(..., gt=0),
    document_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company_for_user(db, company_id, current_user)
    allowed = {"quotation", "order", "delivery", "invoice", "credit_note"}
    if document_type is not None and document_type not in allowed:
        raise HTTPException(400, "Invalid sales document type")
    return _list_documents_for_user(db, company_id, "sale", document_type, current_user)


@router.get("/purchases/documents", response_model=list[DocumentResponse])
def purchases(
    company_id: int = Query(..., gt=0),
    document_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company_for_user(db, company_id, current_user)
    allowed = {"requisition", "rfq", "order", "receipt", "bill", "debit_note"}
    if document_type is not None and document_type not in allowed:
        raise HTTPException(400, "Invalid purchase document type")
    return _list_documents_for_user(db, company_id, "purchase", document_type, current_user)

@router.post("/sales/{document_id}/cancel", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.post"))])
def cancel_sales_order(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "sale", current_user)
    order = _run(lambda: commerce_service.cancel_sales_order(db, company_id=company_id, document_id=document_id))
    db.commit(); db.refresh(order); return order


@router.post("/sales/{document_id}/confirm", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.post"))])
def confirm_sale(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "sale", current_user)
    def action():
        obj = db.scalar(select(SalesDocument).where(SalesDocument.id == document_id, SalesDocument.company_id == company_id).with_for_update())
        if obj is None: raise ValueError("Document not found")
        snapshot = capture_document_tax_snapshot(db, obj, kind="sale")
        if snapshot is None: raise ValueError("A jurisdiction tax snapshot is required before posting this sales document")
        validate_document_tax_snapshot(obj, snapshot)
        return commerce_service.confirm(db, company_id, document_id, "sale", current_user.id)
    obj = _run(action); db.commit(); db.refresh(obj); return obj


@router.post("/purchases/{document_id}/confirm", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.post"))])
def confirm_purchase(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "purchase", current_user)
    def action():
        obj = db.scalar(select(PurchaseDocument).where(PurchaseDocument.id == document_id, PurchaseDocument.company_id == company_id).with_for_update())
        if obj is None: raise ValueError("Document not found")
        snapshot = capture_document_tax_snapshot(db, obj, kind="purchase")
        if snapshot is None: raise ValueError("A jurisdiction tax snapshot is required before posting this purchase document")
        validate_document_tax_snapshot(obj, snapshot)
        return commerce_service.confirm(db, company_id, document_id, "purchase", current_user.id)
    obj = _run(action); db.commit(); db.refresh(obj); return obj






@router.get("/sales/{document_id}/approval-events")
def list_sales_order_approval_events(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "sale", current_user)
    return _run(lambda: commerce_service.list_approval_events(db, company_id, document_id, "sale"))


@router.get("/purchases/{document_id}/approval-events")
def list_purchase_order_approval_events(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "purchase", current_user)
    return _run(lambda: commerce_service.list_approval_events(db, company_id, document_id, "purchase"))


@router.post("/sales/{document_id}/approval-decision", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.post"))])
def decide_sales_order_approval(document_id: int, payload: CommerceApprovalDecision, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "sale", current_user)
    obj = _run(lambda: commerce_service.decide_approval(db, company_id, document_id, "sale", payload.decision, current_user.id, payload.reason))
    db.commit(); db.refresh(obj); return obj


@router.post("/purchases/{document_id}/approval-decision", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.post"))])
def decide_purchase_order_approval(document_id: int, payload: CommerceApprovalDecision, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "purchase", current_user)
    obj = _run(lambda: commerce_service.decide_approval(db, company_id, document_id, "purchase", payload.decision, current_user.id, payload.reason))
    db.commit(); db.refresh(obj); return obj


@router.post("/sales/{document_id}/post-inventory", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.post"))])
def post_sale(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "sale", current_user); obj = _run(lambda: commerce_service.post_inventory(db, company_id, document_id, "sale", user_id=current_user.id)); db.commit(); db.refresh(obj); return obj


@router.post("/purchases/{document_id}/receive", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.post"))])
def receive_purchase(document_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    _assert_document_access(db, company_id, document_id, "purchase", current_user); obj = _run(lambda: commerce_service.post_inventory(db, company_id, document_id, "purchase", user_id=current_user.id)); db.commit(); db.refresh(obj); return obj


@router.get("/payments", response_model=list[PaymentResponse])
def list_payments(company_id: int = Query(..., gt=0), document_kind: str | None = Query(default=None, pattern="^(sale|purchase)$"), document_id: int | None = Query(default=None, gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    if document_id is not None:
        if document_kind is None:
            raise HTTPException(422, "document_kind is required when filtering payments by document_id")
        _assert_document_access(db, company_id, document_id, document_kind, current_user)
    query = select(CommercePayment).where(CommercePayment.company_id == company_id)
    if document_kind:
        query = query.where(CommercePayment.document_kind == document_kind)
    if document_id:
        query = query.where(CommercePayment.document_id == document_id)
    if not current_user.is_platform_admin:
        context = get_optional_request_context()
        if context is None or context.branch_id is None:
            raise HTTPException(400, "Select a branch using X-Branch-ID before listing payments")
        require_branch_access(db, company_id, context.branch_id, current_user)
        sales_ids = select(SalesDocument.id).outerjoin(
            InventoryWarehouse, InventoryWarehouse.id == SalesDocument.warehouse_id
        ).where(
            SalesDocument.company_id == company_id,
            or_(
                SalesDocument.warehouse_id.is_(None),
                InventoryWarehouse.is_central.is_(True),
                InventoryWarehouse.branch_id == context.branch_id,
            ),
        )
        purchase_ids = select(PurchaseDocument.id).outerjoin(
            InventoryWarehouse, InventoryWarehouse.id == PurchaseDocument.warehouse_id
        ).where(
            PurchaseDocument.company_id == company_id,
            or_(
                PurchaseDocument.warehouse_id.is_(None),
                InventoryWarehouse.is_central.is_(True),
                InventoryWarehouse.branch_id == context.branch_id,
            ),
        )
        query = query.where(or_(
            and_(CommercePayment.document_kind == "sale", CommercePayment.document_id.in_(sales_ids)),
            and_(CommercePayment.document_kind == "purchase", CommercePayment.document_id.in_(purchase_ids)),
        ))
    return list(db.scalars(query.order_by(CommercePayment.id.desc()).limit(500)).all())


@router.post("/sales/{document_id}/payments", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.payment"))])
def pay_sale(document_id: int, payload: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.document_id != document_id: raise HTTPException(400, "Document id mismatch")
    _company_for_user(db, payload.company_id, current_user); _assert_document_access(db, payload.company_id, document_id, "sale", current_user); obj, payment = _run(lambda: commerce_service.pay(db, payload, "sale", current_user.id)); db.commit(); db.refresh(obj); return obj


@router.post("/purchases/{document_id}/payments", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.payment"))])
def pay_purchase(document_id: int, payload: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.document_id != document_id: raise HTTPException(400, "Document id mismatch")
    _company_for_user(db, payload.company_id, current_user); _assert_document_access(db, payload.company_id, document_id, "purchase", current_user); obj, payment = _run(lambda: commerce_service.pay(db, payload, "purchase", current_user.id)); db.commit(); db.refresh(obj); return obj


@router.post("/payments/{payment_id}/reverse", response_model=DocumentResponse, dependencies=[Depends(require_permission("commerce.reverse"))])
def reverse_payment(payment_id: int, payload: PaymentReverse, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    original = db.scalar(select(CommercePayment).where(CommercePayment.id == payment_id, CommercePayment.company_id == payload.company_id))
    if original is None: raise HTTPException(404, "Payment not found")
    _assert_document_access(
        db,
        payload.company_id,
        original.document_id,
        "sale" if original.document_kind == "sale" else "purchase",
        current_user,
    )
    obj, original, reversal = _run(lambda: commerce_service.reverse_payment(db, payload.company_id, payment_id, payload.reversal_date, payload.notes, current_user.id)); db.commit(); db.refresh(obj); return obj
