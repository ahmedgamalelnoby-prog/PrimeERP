from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.accounting.models import TaxRate
from app.modules.accounting.tax_engine import calculate_taxes
from app.modules.catalog.models import ProductVariant
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.models import BusinessPartner, SalesDocument, SalesLine
from app.modules.commerce.sales_return_accounting import post_sales_return_cogs
from app.modules.commerce.sales_return_models import SalesReturnAllocation
from app.modules.commerce.sales_return_schemas import SalesReturnCreate
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.warehouses.models import InventoryWarehouse


class SalesReturnService:
    def _source_line(self, db: Session, company_id: int, line_id: int):
        row = db.scalar(select(SalesLine, SalesDocument).join(SalesDocument, SalesDocument.id == SalesLine.document_id).where(SalesLine.id == line_id, SalesDocument.company_id == company_id, SalesDocument.document_type == "delivery").with_for_update())
        if row is None:
            raise ValueError(f"Original delivery line {line_id} was not found")
        line, delivery = row
        if delivery.status not in {"fulfilled", "partially_fulfilled"}:
            raise ValueError("Only posted/fulfilled delivery lines can be returned")
        return line, delivery

    def _validate_variant(self, db: Session, company_id: int, item_id: int, variant_id: int | None):
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == item_id, InventoryItem.company_id == company_id, InventoryItem.is_active.is_(True)))
        if item is None:
            raise ValueError(f"Item {item_id} was not found")
        active_variant = db.scalar(select(ProductVariant.id).where(ProductVariant.company_id == company_id, ProductVariant.product_id == item_id, ProductVariant.is_active.is_(True)).limit(1))
        if active_variant is not None and variant_id is None:
            raise ValueError("Original delivery line must identify an active product variant")
        if variant_id is not None and db.scalar(select(ProductVariant.id).where(ProductVariant.id == variant_id, ProductVariant.company_id == company_id, ProductVariant.product_id == item_id, ProductVariant.is_active.is_(True))) is None:
            raise ValueError("Original delivery variant is invalid or inactive")

    def create_and_post(self, db: Session, payload: SalesReturnCreate, user_id: int):
        partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == payload.partner_id, BusinessPartner.company_id == payload.company_id, BusinessPartner.is_active.is_(True)).with_for_update())
        if partner is None or partner.partner_type not in {"customer", "both"}:
            raise ValueError("Customer was not found or is not valid for sales returns")
        if db.scalar(select(SalesDocument.id).where(SalesDocument.company_id == payload.company_id, SalesDocument.number == payload.number)):
            raise ValueError("Document number already exists")
        if len({line.original_delivery_line_id for line in payload.lines}) != len(payload.lines):
            raise ValueError("Each original delivery line may appear only once in a return")
        source_rows = []
        destination_warehouse_id = payload.warehouse_id
        for request_line in payload.lines:
            source_line, delivery = self._source_line(db, payload.company_id, request_line.original_delivery_line_id)
            if delivery.partner_id != payload.partner_id:
                raise ValueError("All returned lines must belong to the selected customer")
            self._validate_variant(db, payload.company_id, source_line.item_id, source_line.variant_id)
            if destination_warehouse_id is None:
                destination_warehouse_id = delivery.warehouse_id
            if destination_warehouse_id is not None and delivery.warehouse_id is None:
                raise ValueError("Original delivery has no warehouse")
            source_rows.append((request_line, source_line, delivery))
        if destination_warehouse_id is None:
            raise ValueError("Return warehouse is required")
        warehouse = db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.id == destination_warehouse_id, InventoryWarehouse.company_id == payload.company_id, InventoryWarehouse.is_active.is_(True)))
        if warehouse is None:
            raise ValueError("Return warehouse does not belong to the company or is inactive")
        locations = list(db.scalars(select(InventoryLocation).where(InventoryLocation.warehouse_id == destination_warehouse_id, InventoryLocation.company_id == payload.company_id, InventoryLocation.is_active.is_(True)).order_by(InventoryLocation.id)).all())
        if not locations:
            raise ValueError("Return warehouse has no active location")
        destination_location_id = locations[0].id
        document = SalesDocument(company_id=payload.company_id, partner_id=payload.partner_id, document_type="credit_note", number=payload.number, document_date=payload.document_date, status="draft", warehouse_id=destination_warehouse_id, notes=payload.notes)
        db.add(document); db.flush()
        for request_line, source_line, _delivery in source_rows:
            tax_ids = list(source_line.tax_rate_ids or [])
            if not tax_ids and source_line.tax_rate_id:
                tax_ids = [source_line.tax_rate_id]
            active_taxes = []
            if tax_ids:
                active_taxes = list(db.scalars(select(TaxRate).where(TaxRate.company_id == payload.company_id, TaxRate.id.in_(tax_ids), TaxRate.is_active.is_(True))).all())
                if {tax.id for tax in active_taxes} != set(tax_ids):
                    raise ValueError("Original tax master is no longer active; return cannot be posted")
            gross = Decimal(request_line.quantity) * Decimal(source_line.unit_price)
            discount = gross * Decimal(source_line.discount_percent or 0) / Decimal("100")
            net = gross - discount
            tax_amount = Decimal(calculate_taxes(db, company_id=payload.company_id, amount=net, tax_ids=tax_ids, inclusive=False)["tax_total"])
            non_wht = [tax for tax in active_taxes if not tax.is_withholding]
            primary_tax_id = non_wht[0].id if non_wht else (tax_ids[0] if tax_ids else None)
            primary_tax_percent = Decimal(next((tax.rate for tax in active_taxes if tax.id == primary_tax_id), 0)) if tax_ids else Decimal("0")
            document.lines.append(SalesLine(item_id=source_line.item_id, variant_id=source_line.variant_id, tax_rate_id=primary_tax_id, tax_rate_ids=tax_ids, description=source_line.description, quantity=request_line.quantity, unit_price=source_line.unit_price, discount_percent=source_line.discount_percent, tax_percent=primary_tax_percent, line_total=net + tax_amount))
            document.subtotal = Decimal(document.subtotal or 0) + net
            document.discount_total = Decimal(document.discount_total or 0) + discount
            document.tax_total = Decimal(document.tax_total or 0) + tax_amount
        document.total = Decimal(document.subtotal) + Decimal(document.tax_total); db.flush()
        for index, (request_line, source_line, delivery) in enumerate(source_rows):
            credit_line = document.lines[index]
            delivery_move = db.scalar(select(InventoryStockMove).where(InventoryStockMove.company_id == payload.company_id, InventoryStockMove.source_module == "commerce", InventoryStockMove.source_entity == "sales_delivery", InventoryStockMove.source_id == f"{delivery.id}:{source_line.id}", InventoryStockMove.status == "posted", InventoryStockMove.item_id == source_line.item_id, InventoryStockMove.variant_id == source_line.variant_id).with_for_update())
            if delivery_move is None:
                raise ValueError(f"Posted inventory movement for delivery line {source_line.id} was not found")
            returned_qty = db.scalar(select(func.coalesce(func.sum(SalesReturnAllocation.quantity), 0)).where(SalesReturnAllocation.company_id == payload.company_id, SalesReturnAllocation.original_delivery_line_id == source_line.id)) or Decimal("0")
            available = Decimal(delivery_move.quantity) - Decimal(returned_qty)
            if Decimal(request_line.quantity) > available:
                raise ValueError(f"return quantity exceeds delivered quantity for line {source_line.id}; available {available}")
            move = inventory_stock_move_service.create_draft(db, StockMoveCreate(company_id=payload.company_id, item_id=source_line.item_id, variant_id=source_line.variant_id, movement_type="receipt", source_location_id=None, destination_location_id=destination_location_id, quantity=request_line.quantity, unit_cost=Decimal(delivery_move.unit_cost or 0), reference=document.number, source_module="commerce", source_entity="sales_return", source_id=f"{document.id}:{credit_line.id}", notes=f"Return against delivery {delivery.number}"))
            inventory_stock_move_service.post(db, company_id=payload.company_id, move_id=move.id)
            db.add(SalesReturnAllocation(company_id=payload.company_id, credit_note_line_id=credit_line.id, original_delivery_line_id=source_line.id, quantity=request_line.quantity, unit_cost=Decimal(delivery_move.unit_cost or 0)))
        document.status = "fulfilled"; db.flush()
        commerce_accounting_service.post_sales_credit_note(db, document, user_id)
        post_sales_return_cogs(db, document, user_id)
        return document


sales_return_service = SalesReturnService()
