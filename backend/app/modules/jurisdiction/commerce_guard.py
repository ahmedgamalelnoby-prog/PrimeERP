from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from app.modules.commerce.models import BusinessPartner, PurchaseDocument, SalesDocument
from .models import PartnerJurisdiction, TaxSnapshot
from .service import JurisdictionContext
from .snapshot_service import TaxSnapshotService
from .tax_posting_guard import validate_snapshot_tax


POSTABLE_SALES = {"invoice", "credit_note"}
POSTABLE_PURCHASES = {"bill", "debit_note"}


def capture_document_tax_snapshot(db: Session, document, *, kind: str) -> TaxSnapshot | None:
    """Capture and validate jurisdiction/tax facts before a financial document is confirmed."""
    if kind == "sale":
        if not isinstance(document, SalesDocument) or document.document_type not in POSTABLE_SALES:
            return None
    elif kind == "purchase":
        if not isinstance(document, PurchaseDocument) or document.document_type not in POSTABLE_PURCHASES:
            return None
    else:
        raise ValueError("Unsupported commerce document kind")

    partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == document.partner_id, BusinessPartner.company_id == document.company_id, BusinessPartner.is_active.is_(True)))
    if partner is None:
        raise ValueError("Partner required for tax jurisdiction resolution")
    registration = db.scalar(select(PartnerJurisdiction).where(and_(PartnerJurisdiction.partner_id == partner.id, PartnerJurisdiction.effective_from <= document.document_date, PartnerJurisdiction.effective_to.is_(None) | (PartnerJurisdiction.effective_to >= document.document_date), PartnerJurisdiction.is_active.is_(True), PartnerJurisdiction.vat_registered.is_(True))).order_by(PartnerJurisdiction.effective_from.desc()))
    b2b = bool(registration or partner.tax_number)
    context = JurisdictionContext(
        company_id=document.company_id,
        partner_id=document.partner_id,
        transaction_type=document.document_type,
        transaction_date=document.document_date,
        place_of_supply=getattr(document, "place_of_supply", None),
        b2b=b2b,
        goods_or_services=getattr(document, "goods_or_services", "goods"),
        import_export=getattr(document, "import_export", None),
        facts={
            "document_subtotal": str(document.subtotal),
            "document_total": str(document.total),
            "tax_total": str(document.tax_total),
            "partner_tax_number_present": bool(partner.tax_number),
        },
    )
    snapshot = TaxSnapshotService(db).capture(document_kind=kind, document_id=document.id, ctx=context)
    validate_snapshot_tax(document, snapshot)
    return snapshot


def validate_document_tax_snapshot(document, snapshot: TaxSnapshot) -> None:
    validate_snapshot_tax(document, snapshot)
