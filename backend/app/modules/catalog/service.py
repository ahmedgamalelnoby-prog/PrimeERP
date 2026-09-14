from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.branches.models import Branch
from app.modules.catalog.models import Menu, MenuItem, ProductCategory, ProductCostHistory, ProductPrice, ProductPriceList, Recipe, RecipeLine
from app.modules.companies.models import Company
from app.modules.inventory.items.models import InventoryItem, InventoryStock

MONEY = Decimal("0.0001")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _money(value: Decimal) -> Decimal:
    return Decimal(value or 0).quantize(MONEY, rounding=ROUND_HALF_UP)


class CatalogService:
    def _company(self, db: Session, company_id: int) -> Company:
        company = db.scalar(select(Company).where(Company.id == company_id, Company.is_active.is_(True)))
        if company is None:
            raise ValueError("Company not found or inactive")
        return company

    def _product(self, db: Session, company_id: int, product_id: int) -> InventoryItem:
        product = db.scalar(select(InventoryItem).where(InventoryItem.id == product_id, InventoryItem.company_id == company_id))
        if product is None:
            raise ValueError("Product not found in this company")
        return product

    def create_category(self, db: Session, payload):
        self._company(db, payload.company_id)
        if payload.parent_id:
            parent = db.scalar(select(ProductCategory).where(ProductCategory.id == payload.parent_id, ProductCategory.company_id == payload.company_id))
            if parent is None:
                raise ValueError("Parent category does not belong to this company")
        category = ProductCategory(**payload.model_dump())
        db.add(category)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ValueError("Category code already exists for this company")
        db.refresh(category)
        return category

    def list_categories(self, db: Session, company_id: int):
        self._company(db, company_id)
        return list(db.scalars(select(ProductCategory).where(ProductCategory.company_id == company_id).order_by(ProductCategory.code)).all())

    def create_price_list(self, db: Session, payload):
        self._company(db, payload.company_id)
        if payload.is_default:
            defaults = db.scalars(select(ProductPriceList).where(ProductPriceList.company_id == payload.company_id, ProductPriceList.is_default.is_(True)).with_for_update()).all()
            for existing in defaults:
                existing.is_default = False
        price_list = ProductPriceList(**payload.model_dump())
        db.add(price_list)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise ValueError("Price list code already exists or another default price list was created concurrently")
        db.refresh(price_list)
        return price_list

    def list_price_lists(self, db: Session, company_id: int):
        self._company(db, company_id)
        return list(db.scalars(select(ProductPriceList).where(ProductPriceList.company_id == company_id, ProductPriceList.is_active.is_(True)).order_by(ProductPriceList.name)).all())

    def set_base_price(self, db: Session, company_id: int, product_id: int, sale_price: Decimal, source: str = "manual"):
        product = self._product(db, company_id, product_id)
        now = _now()
        price_list = self._default_price_list(db, company_id)
        previous = db.scalars(select(ProductPrice).where(ProductPrice.company_id == company_id, ProductPrice.price_list_id == price_list.id, ProductPrice.product_id == product_id, ProductPrice.min_quantity == 1, ProductPrice.is_active.is_(True), ProductPrice.valid_to.is_(None)).with_for_update()).all()
        for row in previous:
            row.valid_to = now
        product.sales_price = _money(sale_price)
        history = ProductPrice(company_id=company_id, price_list_id=price_list.id, product_id=product_id, sale_price=product.sales_price, min_quantity=1, source=source, valid_from=now)
        db.add(history)
        db.commit()
        db.refresh(product)
        return product

    def _default_price_list(self, db: Session, company_id: int) -> ProductPriceList:
        price_list = db.scalar(select(ProductPriceList).where(ProductPriceList.company_id == company_id, ProductPriceList.is_default.is_(True), ProductPriceList.is_active.is_(True)).with_for_update())
        if price_list is None:
            price_list = ProductPriceList(company_id=company_id, code="DEFAULT", name="Default Price List", currency="EGP", channel="default", is_default=True)
            db.add(price_list)
            db.flush()
        return price_list

    def create_price(self, db: Session, company_id: int, payload):
        self._product(db, company_id, payload.product_id)
        price_list = db.scalar(select(ProductPriceList).where(ProductPriceList.id == payload.price_list_id, ProductPriceList.company_id == company_id, ProductPriceList.is_active.is_(True)))
        if price_list is None:
            raise ValueError("Price list does not belong to this company")
        valid_from = payload.valid_from or _now()
        if payload.valid_to and payload.valid_to <= valid_from:
            raise ValueError("valid_to must be after valid_from")
        overlap = db.scalar(select(ProductPrice).where(ProductPrice.company_id == company_id, ProductPrice.price_list_id == payload.price_list_id, ProductPrice.product_id == payload.product_id, ProductPrice.min_quantity == payload.min_quantity, ProductPrice.is_active.is_(True), ProductPrice.valid_from < (payload.valid_to or datetime.max), (ProductPrice.valid_to.is_(None)) | (ProductPrice.valid_to > valid_from)).with_for_update())
        if overlap is not None:
            raise ValueError("Overlapping active price period exists")
        price = ProductPrice(company_id=company_id, **payload.model_dump(exclude={"valid_from", "valid_to"}), valid_from=valid_from, valid_to=payload.valid_to)
        db.add(price)
        db.commit()
        db.refresh(price)
        return price

    def record_cost(self, db: Session, company_id: int, payload):
        self._product(db, company_id, payload.product_id)
        row = ProductCostHistory(company_id=company_id, **payload.model_dump(exclude={"effective_at"}), effective_at=payload.effective_at or _now())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def create_recipe(self, db: Session, payload):
        self._product(db, payload.company_id, payload.product_id)
        ingredient_ids = [line.ingredient_product_id for line in payload.lines]
        if not ingredient_ids:
            raise ValueError("Recipe must contain at least one ingredient")
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValueError("Duplicate ingredient products are not allowed in one recipe")
        if payload.product_id in ingredient_ids:
            raise ValueError("A product cannot directly contain itself as an ingredient")
        ingredients = list(db.scalars(select(InventoryItem).where(InventoryItem.company_id == payload.company_id, InventoryItem.id.in_(ingredient_ids), InventoryItem.is_active.is_(True))).all())
        if len(ingredients) != len(set(ingredient_ids)):
            raise ValueError("One or more recipe ingredients are invalid or inactive")
        current = db.scalar(select(Recipe).where(Recipe.company_id == payload.company_id, Recipe.product_id == payload.product_id, Recipe.is_active.is_(True)).order_by(Recipe.version.desc()).limit(1).with_for_update())
        version = (current.version + 1) if current else 1
        if current:
            current.is_active = False
        recipe = Recipe(company_id=payload.company_id, product_id=payload.product_id, code=payload.code, name_ar=payload.name_ar, name_en=payload.name_en, yield_quantity=payload.yield_quantity, waste_percentage=payload.waste_percentage, version=version, is_active=True)
        for line_no, line in enumerate(payload.lines, start=1):
            recipe.lines.append(RecipeLine(line_no=line_no, **line.model_dump()))
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        return self.get_recipe(db, payload.company_id, recipe.id)

    def get_recipe(self, db: Session, company_id: int, recipe_id: int):
        recipe = db.scalar(select(Recipe).options(selectinload(Recipe.lines)).where(Recipe.id == recipe_id, Recipe.company_id == company_id))
        if recipe is None:
            raise ValueError("Recipe not found")
        return recipe

    def list_recipes(self, db: Session, company_id: int):
        self._company(db, company_id)
        return list(db.scalars(select(Recipe).options(selectinload(Recipe.lines)).where(Recipe.company_id == company_id, Recipe.is_active.is_(True)).order_by(Recipe.product_id)).all())

    def ingredient_unit_cost(self, db: Session, company_id: int, product_id: int) -> Decimal:
        product = self._product(db, company_id, product_id)
        average = db.scalar(select(func.avg(InventoryStock.average_cost)).where(InventoryStock.company_id == company_id, InventoryStock.item_id == product_id))
        if average is not None and Decimal(average) > 0:
            return _money(Decimal(average))
        return _money(Decimal(product.standard_cost or product.purchase_price or 0))

    def recipe_cost(self, db: Session, company_id: int, recipe_id: int) -> Decimal:
        recipe = self.get_recipe(db, company_id, recipe_id)
        total = Decimal("0")
        for line in recipe.lines:
            unit_cost = self.ingredient_unit_cost(db, company_id, line.ingredient_product_id)
            factor = Decimal("1") + (Decimal(line.waste_percentage or 0) / Decimal("100"))
            total += Decimal(line.quantity) * factor * unit_cost
        recipe_factor = Decimal("1") + (Decimal(recipe.waste_percentage or 0) / Decimal("100"))
        return _money((total * recipe_factor) / Decimal(recipe.yield_quantity))

    def create_menu(self, db: Session, payload):
        self._company(db, payload.company_id)
        if payload.branch_id:
            branch = db.scalar(select(Branch).where(Branch.id == payload.branch_id, Branch.company_id == payload.company_id, Branch.is_active.is_(True)))
            if branch is None:
                raise ValueError("Branch does not belong to this company")
        menu = Menu(**payload.model_dump())
        db.add(menu)
        db.commit()
        db.refresh(menu)
        return self.get_menu(db, payload.company_id, menu.id)

    def get_menu(self, db: Session, company_id: int, menu_id: int):
        menu = db.scalar(select(Menu).options(selectinload(Menu.items)).where(Menu.id == menu_id, Menu.company_id == company_id))
        if menu is None:
            raise ValueError("Menu not found")
        return menu

    def add_menu_item(self, db: Session, company_id: int, menu_id: int, payload):
        menu = self.get_menu(db, company_id, menu_id)
        self._product(db, company_id, payload.product_id)
        if payload.price_list_id:
            price_list = db.scalar(select(ProductPriceList).where(ProductPriceList.id == payload.price_list_id, ProductPriceList.company_id == company_id, ProductPriceList.is_active.is_(True)))
            if price_list is None:
                raise ValueError("Price list does not belong to this company")
        item = MenuItem(menu_id=menu.id, **payload.model_dump())
        db.add(item)
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise ValueError("Product is already on this menu or menu item is invalid") from exc
        db.refresh(item)
        return item

    def pricing_analysis(self, db: Session, company_id: int, product_id: int, target_margin: Decimal = Decimal("30")):
        product = self._product(db, company_id, product_id)
        current_cost = self.ingredient_unit_cost(db, company_id, product_id)
        recipe = db.scalar(select(Recipe).where(Recipe.company_id == company_id, Recipe.product_id == product_id, Recipe.is_active.is_(True)).order_by(Recipe.version.desc()))
        recipe_cost = self.recipe_cost(db, company_id, recipe.id) if recipe else None
        if recipe_cost is not None:
            current_cost = recipe_cost
        now = _now()
        price = db.scalar(select(ProductPrice).where(ProductPrice.company_id == company_id, ProductPrice.product_id == product_id, ProductPrice.is_active.is_(True), ProductPrice.valid_from <= now, ((ProductPrice.valid_to.is_(None)) | (ProductPrice.valid_to > now))).order_by(ProductPrice.min_quantity.desc(), ProductPrice.valid_from.desc()))
        sale_price = _money(price.sale_price if price else product.sales_price)
        margin = _money(sale_price - current_cost)
        margin_pct = _money((margin / sale_price * 100) if sale_price > 0 else 0)
        recommended = _money(current_cost / (Decimal("1") - target_margin / Decimal("100"))) if target_margin < 100 else None
        prices = list(db.scalars(select(ProductPrice).where(ProductPrice.company_id == company_id, ProductPrice.product_id == product_id).order_by(ProductPrice.valid_from.desc()).limit(50)).all())
        costs = list(db.scalars(select(ProductCostHistory).where(ProductCostHistory.company_id == company_id, ProductCostHistory.product_id == product_id).order_by(ProductCostHistory.effective_at.desc()).limit(50)).all())
        return {
            "product_id": product.id,
            "product_name": product.name_en or product.name_ar,
            "current_cost": current_cost,
            "sale_price": sale_price,
            "gross_margin": margin,
            "gross_margin_percentage": margin_pct,
            "recommended_price_at_margin": recommended,
            "recipe_cost": recipe_cost,
            "price_history": [{"id": p.id, "sale_price": p.sale_price, "valid_from": p.valid_from, "valid_to": p.valid_to, "min_quantity": p.min_quantity, "source": p.source} for p in prices],
            "cost_history": [{"id": c.id, "cost": c.cost, "cost_type": c.cost_type, "effective_at": c.effective_at, "source": c.source} for c in costs],
        }


catalog_service = CatalogService()
