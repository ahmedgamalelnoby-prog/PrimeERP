from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.commerce.models import PurchaseDocument, SalesDocument
from .models import TaxSnapshot
from .service import JurisdictionContext
from .snapshot_service import TaxSnapshotService


POSTABLE_SALES = {"invoice", "credit_note"}
POSTABLE_PURCHASES = {"bill", "debit_note"}


def capture_document_tax_snapshot(db: Session, document, *, kind: str) -> TaxSnapshot | None:
    """Capture jurisdiction/tax facts before a commercial document is confirmed."""
    if kind == "sale":
        if not isinstance(document, SalesDocument) or document.document_type not in POSTABLE_SALES:
            return None
    elif kind == "purchase":
        if not isinstance(document, PurchaseDocument) or document.document_type not in POSTABLE_PURCHASES:
            return None
    else:
        raise ValueError("Unsupported commerce document kind")

    context = JurisdictionContext(
        company_id=document.company_id,
        partner_id=document.partner_id,
        transaction_type=document.document_type,
        transaction_date=document.document_date,
        place_of_supply=getattr(document, "place_of_supply", None),
        b2b=True,
        goods_or_services="goods",
        facts={"document_total": str(document.total), "tax_total": str(document.tax_total)},
    )
    return TaxSnapshotService(db).capture(
        document_kind="sale" if kind == "sale" else "purchase",
        document_id=document.id,
        context=context,
    )
