from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import ProductPrice, ProductPriceList
from app.modules.catalog.service import catalog_service
from app.modules.inventory.items.models import InventoryItem

MONEY = Decimal("0.0001")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _money(value: Decimal) -> Decimal:
    return Decimal(value or 0).quantize(MONEY, rounding=ROUND_HALF_UP)


class PricingEngine:
    """Canonical read-side pricing resolver and product-wide margin scanner."""

    def _price_list(self, db: Session, company_id: int, price_list_id: int | None) -> ProductPriceList | None:
        if price_list_id is None:
            return db.scalar(select(ProductPriceList).where(ProductPriceList.company_id == company_id, ProductPriceList.is_default.is_(True), ProductPriceList.is_active.is_(True)))
        return db.scalar(select(ProductPriceList).where(ProductPriceList.id == price_list_id, ProductPriceList.company_id == company_id, ProductPriceList.is_active.is_(True)))

    def resolve_price(self, db: Session, company_id: int, product_id: int, quantity: Decimal = Decimal("1"), price_list_id: int | None = None, at: datetime | None = None) -> dict:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        product = catalog_service._product(db, company_id, product_id)
        price_list = self._price_list(db, company_id, price_list_id)
        if price_list_id is not None and price_list is None:
            raise ValueError("Price list does not belong to this company")
        selected_list_id = price_list.id if price_list else None
        moment = at or _now()
        if selected_list_id is None:
            return {"product_id": product.id, "price_list_id": None, "quantity": quantity, "unit_price": _money(product.sales_price), "source": "product_base_price", "price_id": None, "currency": "EGP"}
        query = select(ProductPrice).where(ProductPrice.company_id == company_id, ProductPrice.product_id == product_id, ProductPrice.price_list_id == selected_list_id, ProductPrice.is_active.is_(True), ProductPrice.valid_from <= moment, (ProductPrice.valid_to.is_(None) | (ProductPrice.valid_to > moment)), ProductPrice.min_quantity <= quantity)
        price = db.scalar(query.order_by(ProductPrice.min_quantity.desc(), ProductPrice.valid_from.desc(), ProductPrice.id.desc()).limit(1))
        if price is None:
            raise ValueError("No active price is applicable for this quantity and price list")
        return {"product_id": product.id, "price_list_id": selected_list_id, "quantity": quantity, "unit_price": _money(price.sale_price), "source": price.source, "price_id": price.id, "currency": price_list.currency}

    def product_wide_impact(self, db: Session, company_id: int, target_margin: Decimal = Decimal("30"), below_margin: Decimal | None = None, price_list_id: int | None = None, quantity: Decimal = Decimal("1")) -> dict:
        if not 0 <= target_margin < 100:
            raise ValueError("Target margin must be between 0 and 100")
        if below_margin is None:
            below_margin = target_margin
        if not 0 <= below_margin < 100:
            raise ValueError("Below-margin threshold must be between 0 and 100")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        products = db.scalars(select(InventoryItem).where(InventoryItem.company_id == company_id, InventoryItem.is_active.is_(True)).order_by(InventoryItem.id)).all()
        impacted = []
        unresolved = []
        for product in products:
            try:
                analysis = catalog_service.pricing_analysis(db, company_id, product.id, target_margin, price_list_id, quantity)
                resolved = self.resolve_price(db, company_id, product.id, quantity, price_list_id)
                cost = Decimal(analysis["current_cost"])
                price = Decimal(resolved["unit_price"])
                margin = _money(price - cost)
                margin_pct = _money((margin / price * 100) if price > 0 else 0)
                recommended = _money(cost / (Decimal("1") - target_margin / 100))
                if margin_pct < below_margin:
                    impacted.append({"product_id": product.id, "product_name": product.name_en or product.name_ar, "price_list_id": resolved["price_list_id"], "quantity": quantity, "price_id": resolved["price_id"], "current_cost": cost, "unit_price": price, "gross_margin": margin, "gross_margin_percentage": margin_pct, "recommended_price_at_margin": recommended, "price_gap": _money(recommended - price)})
            except ValueError as exc:
                unresolved.append({"product_id": product.id, "product_name": product.name_en or product.name_ar, "error": str(exc)})
        impacted.sort(key=lambda row: (row["gross_margin_percentage"], row["product_id"]))
        return {"target_margin": target_margin, "below_margin": below_margin, "price_list_id": price_list_id, "quantity": quantity, "count": len(impacted), "items": impacted, "unresolved_count": len(unresolved), "unresolved": unresolved}


pricing_engine = PricingEngine()
