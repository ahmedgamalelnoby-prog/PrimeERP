from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.modules.accounting.models import TaxRate
from app.modules.accounting.tax_engine import calculate_taxes
from app.modules.catalog.models import ProductVariant
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.models import BusinessPartner, PurchaseDocument, PurchaseLine
from app.modules.commerce.purchase_return_models import PurchaseReturnAllocation
from app.modules.commerce.purchase_return_schemas import PurchaseReturnCreate
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.audit.service import record_audit_event

class PurchaseReturnService:
    def _source_line(self, db: Session, company_id: int, line_id: int):
        row = db.scalar(select(PurchaseLine, PurchaseDocument).join(PurchaseDocument, PurchaseDocument.id == PurchaseLine.document_id).where(PurchaseLine.id == line_id, PurchaseDocument.company_id == company_id, PurchaseDocument.document_type == "receipt").with_for_update())
        if row is None: raise ValueError(f"Original purchase receipt line {line_id} was not found")
        line, receipt = row
        if receipt.status not in {"received", "partially_received"}: raise ValueError("Only received purchase receipt lines can be returned")
        return line, receipt

    def _validate_variant(self, db, company_id, item_id, variant_id):
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == item_id, InventoryItem.company_id == company_id, InventoryItem.is_active.is_(True)))
        if item is None: raise ValueError(f"Item {item_id} was not found")
        active_variant = db.scalar(select(ProductVariant.id).where(ProductVariant.company_id == company_id, ProductVariant.product_id == item_id, ProductVariant.is_active.is_(True)).limit(1))
        if active_variant is not None and variant_id is None: raise ValueError("Original receipt line must identify an active product variant")
        if variant_id is not None and db.scalar(select(ProductVariant.id).where(ProductVariant.id == variant_id, ProductVariant.company_id == company_id, ProductVariant.product_id == item_id, ProductVariant.is_active.is_(True))) is None: raise ValueError("Original receipt variant is invalid or inactive")

    def create_and_post(self, db: Session, payload: PurchaseReturnCreate, user_id: int, tenant_id: int | None = None):
        partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == payload.partner_id, BusinessPartner.company_id == payload.company_id, BusinessPartner.is_active.is_(True)).with_for_update())
        if partner is None or partner.partner_type not in {"vendor", "both"}: raise ValueError("Vendor was not found or is not valid for purchase returns")
        if db.scalar(select(PurchaseDocument.id).where(PurchaseDocument.company_id == payload.company_id, PurchaseDocument.number == payload.number)): raise ValueError("Document number already exists")
        if len({x.original_receipt_line_id for x in payload.lines}) != len(payload.lines): raise ValueError("Each original receipt line may appear only once in a return")
        rows=[]; warehouse_id=payload.warehouse_id
        for req in payload.lines:
            line, receipt=self._source_line(db,payload.company_id,req.original_receipt_line_id)
            if receipt.partner_id != payload.partner_id: raise ValueError("All returned lines must belong to the selected vendor")
            self._validate_variant(db,payload.company_id,line.item_id,line.variant_id)
            if warehouse_id is None: warehouse_id=receipt.warehouse_id
            rows.append((req,line,receipt))
        if warehouse_id is None: raise ValueError("Return warehouse is required")
        warehouse=db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.id==warehouse_id,InventoryWarehouse.company_id==payload.company_id,InventoryWarehouse.is_active.is_(True)))
        if warehouse is None: raise ValueError("Return warehouse does not belong to the company or is inactive")
        locations=list(db.scalars(select(InventoryLocation).where(InventoryLocation.warehouse_id==warehouse_id,InventoryLocation.company_id==payload.company_id,InventoryLocation.is_active.is_(True)).order_by(InventoryLocation.id)).all())
        if not locations: raise ValueError("Return warehouse has no active location")
        source_location_id=locations[0].id
        document=PurchaseDocument(company_id=payload.company_id,partner_id=payload.partner_id,document_type="debit_note",number=payload.number,document_date=payload.document_date,status="draft",warehouse_id=warehouse_id,notes=payload.notes)
        db.add(document); db.flush()
        for req,line,_receipt in rows:
            tax_ids=list(line.tax_rate_ids or [])
            if not tax_ids and line.tax_rate_id: tax_ids=[line.tax_rate_id]
            active_taxes=list(db.scalars(select(TaxRate).where(TaxRate.company_id==payload.company_id,TaxRate.id.in_(tax_ids),TaxRate.is_active.is_(True))).all()) if tax_ids else []
            if {t.id for t in active_taxes} != set(tax_ids): raise ValueError("Original tax master is no longer active; return cannot be posted")
            gross=Decimal(req.quantity)*Decimal(line.unit_price); discount=gross*Decimal(line.discount_percent or 0)/Decimal("100"); net=gross-discount
            tax_amount=Decimal(calculate_taxes(db,company_id=payload.company_id,amount=net,tax_ids=tax_ids,inclusive=False)["tax_total"])
            non_wht=[t for t in active_taxes if not t.is_withholding]; primary_tax_id=non_wht[0].id if non_wht else (tax_ids[0] if tax_ids else None)
            primary_tax_percent=Decimal(next((t.rate for t in active_taxes if t.id==primary_tax_id),0)) if tax_ids else Decimal("0")
            document.lines.append(PurchaseLine(item_id=line.item_id,variant_id=line.variant_id,tax_rate_id=primary_tax_id,tax_rate_ids=tax_ids,description=line.description,quantity=req.quantity,unit_price=line.unit_price,discount_percent=line.discount_percent,tax_percent=primary_tax_percent,line_total=net+tax_amount))
            document.subtotal=Decimal(document.subtotal or 0)+net; document.discount_total=Decimal(document.discount_total or 0)+discount; document.tax_total=Decimal(document.tax_total or 0)+tax_amount
        document.total=Decimal(document.subtotal)+Decimal(document.tax_total); db.flush()
        for idx,(req,line,receipt) in enumerate(rows):
            debit_line=document.lines[idx]
            receipt_move=db.scalar(select(InventoryStockMove).where(InventoryStockMove.company_id==payload.company_id,InventoryStockMove.source_module=="commerce",InventoryStockMove.source_entity=="purchase_receipt",InventoryStockMove.source_id==f"{receipt.id}:{line.id}",InventoryStockMove.status=="posted",InventoryStockMove.item_id==line.item_id,InventoryStockMove.variant_id==line.variant_id).with_for_update())
            if receipt_move is None: raise ValueError(f"Posted inventory movement for receipt line {line.id} was not found")
            returned=db.scalar(select(func.coalesce(func.sum(PurchaseReturnAllocation.quantity),0)).where(PurchaseReturnAllocation.company_id==payload.company_id,PurchaseReturnAllocation.original_receipt_line_id==line.id)) or Decimal("0")
            available=Decimal(receipt_move.quantity)-Decimal(returned)
            if Decimal(req.quantity)>available: raise ValueError(f"Return quantity exceeds received quantity for line {line.id}; available {available}")
            actual_source_location_id = receipt_move.destination_location_id or source_location_id
            move=inventory_stock_move_service.create_draft(db,StockMoveCreate(company_id=payload.company_id,item_id=line.item_id,variant_id=line.variant_id,movement_type="issue",source_location_id=actual_source_location_id,destination_location_id=None,quantity=req.quantity,unit_cost=Decimal(receipt_move.unit_cost or 0),transaction_date=payload.document_date,reference=document.number,source_module="commerce",source_entity="purchase_return",source_id=f"{document.id}:{debit_line.id}",notes=f"Return against purchase receipt {receipt.number}"))
            inventory_stock_move_service.post(db,company_id=payload.company_id,move_id=move.id,user_id=user_id)
            db.add(PurchaseReturnAllocation(company_id=payload.company_id,debit_note_line_id=debit_line.id,original_receipt_line_id=line.id,quantity=req.quantity,unit_cost=Decimal(receipt_move.unit_cost or 0)))
        document.status="posted"; db.flush()
        commerce_accounting_service.post_purchase_debit_note(db,document,user_id)
        record_audit_event(db,action="commerce.purchase_return.post",entity_type="purchase_debit_note",entity_id=document.id,user_id=user_id,company_id=payload.company_id,metadata={"partner_id":payload.partner_id,"total":str(document.total)})
        return document

purchase_return_service=PurchaseReturnService()
