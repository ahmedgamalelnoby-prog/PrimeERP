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

    def _locked_company(self, db: Session, company_id: int) -> Company:
        company = db.scalar(select(Company).where(Company.id == company_id, Company.is_active.is_(True)).with_for_update())
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
            if payload.parent_id == 0:
                raise ValueError("Parent category is invalid")
            parent = db.scalar(select(ProductCategory).where(ProductCategory.id == payload.parent_id, ProductCategory.company_id == payload.company_id, ProductCategory.is_active.is_(True)))
            if parent is None:
                raise ValueError("Parent category is invalid")
        category = ProductCategory(**payload.model_dump())
        db.add(category)
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise ValueError("Category code already exists for this company") from exc
        db.refresh(category)
        return category

    def list_categories(self, db: Session, company_id: int):
        self._company(db, company_id)
        return list(db.scalars(select(ProductCategory).where(ProductCategory.company_id == company_id).order_by(ProductCategory.code)).all())

    def create_price_list(self, db: Session, payload):
        self._locked_company(db, payload.company_id) if payload.is_default else self._company(db, payload.company_id)
        if payload.is_default:
            defaults = db.scalars(select(ProductPriceList).where(ProductPriceList.company_id == payload.company_id, ProductPriceList.is_default.is_(True)).with_for_update()).all()
            for existing in defaults:
                existing.is_default = False
        price_list = ProductPriceList(**payload.model_dump())
        db.add(price_list)
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise ValueError("Price list code already exists") from exc
        db.refresh(price_list)
        return price_list

    def list_price_lists(self, db: Session, company_id: int):
        self._company(db, company_id)
        return list(db.scalars(select(ProductPriceList).where(ProductPriceList.company_id == company_id).order_by(ProductPriceList.name)).all())

    def set_base_price(self, db: Session, company_id: int, product_id: int, sale_price: Decimal, source: str = "manual"):
        product = self._product(db, company_id, product_id)
        now = _now()
        price_list = self._default_price_list(db, company_id)
        previous = db.scalars(select(ProductPrice).where(ProductPrice.company_id == company_id, ProductPrice.price_list_id == price_list.id, ProductPrice.product_id == product_id, ProductPrice.min_quantity == 1, ProductPrice.is_active.is_(True), ProductPrice.valid_to.is_(None)).with_for_update()).all()
        for row in previous:
            row.valid_to = now
        product.sales_price = _money(sale_price)
        db.add(ProductPrice(company_id=company_id, price_list_id=price_list.id, product_id=product_id, sale_price=product.sales_price, min_quantity=1, source=source, valid_from=now))
        db.commit()
        db.refresh(product)
        return product

    def _default_price_list(self, db: Session, company_id: int) -> ProductPriceList:
        self._locked_company(db, company_id)
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

    def list_prices(self, db: Session, company_id: int, product_id: int | None = None, price_list_id: int | None = None):
        self._company(db, company_id)
        query = select(ProductPrice).where(ProductPrice.company_id == company_id)
        if product_id is not None:
            self._product(db, company_id, product_id)
            query = query.where(ProductPrice.product_id == product_id)
        if price_list_id is not None:
            if db.scalar(select(ProductPriceList.id).where(ProductPriceList.id == price_list_id, ProductPriceList.company_id == company_id)) is None:
                raise ValueError("Price list does not belong to this company")
            query = query.where(ProductPrice.price_list_id == price_list_id)
        return list(db.scalars(query.order_by(ProductPrice.product_id, ProductPrice.valid_from.desc())).all())

    def record_cost(self, db: Session, company_id: int, payload):
        self._product(db, company_id, payload.product_id)
        row = ProductCostHistory(company_id=company_id, **payload.model_dump(exclude={"effective_at"}), effective_at=payload.effective_at or _now())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list_cost_history(self, db: Session, company_id: int, product_id: int):
        self._product(db, company_id, product_id)
        return list(db.scalars(select(ProductCostHistory).where(ProductCostHistory.company_id == company_id, ProductCostHistory.product_id == product_id).order_by(ProductCostHistory.effective_at.desc())).all())

    def create_recipe(self, db: Session, payload):
        self._product(db, payload.company_id, payload.product_id)
        ingredient_ids = [line.ingredient_product_id for line in payload.lines]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValueError("Duplicate ingredient products are not allowed in one recipe")
        if payload.product_id in ingredient_ids:
            raise ValueError("A product cannot directly contain itself as an ingredient")
        ingredients = list(db.scalars(select(InventoryItem).where(InventoryItem.company_id == payload.company_id, InventoryItem.id.in_(ingredient_ids), InventoryItem.is_active.is_(True))).all())
        if len(ingredients) != len(set(ingredient_ids)):
            raise ValueError("One or more recipe ingredients are invalid or inactive")
        for line in payload.lines:
            if line.uom_id is not None:
                from app.modules.uom.models import UnitOfMeasure
                uom = db.scalar(select(UnitOfMeasure).where(UnitOfMeasure.id == line.uom_id, UnitOfMeasure.company_id == payload.company_id, UnitOfMeasure.is_active.is_(True)))
                if uom is None:
                    raise ValueError("Recipe line UOM does not belong to this company")
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

    def _active_recipe_for_product(self, db: Session, company_id: int, product_id: int):
        return db.scalar(select(Recipe).options(selectinload(Recipe.lines)).where(Recipe.company_id == company_id, Recipe.product_id == product_id, Recipe.is_active.is_(True)).order_by(Recipe.version.desc()))

    def ingredient_unit_cost(self, db: Session, company_id: int, product_id: int, _visited: set[int] | None = None) -> Decimal:
        product = self._product(db, company_id, product_id)
        visited = set(_visited or ())
        if product_id in visited:
            raise ValueError("Recipe cycle detected while calculating product cost")
        visited.add(product_id)

        # A product with an active recipe is a manufactured/menu product. Its
        # effective cost is calculated from its current ingredient tree.
        active_recipe = self._active_recipe_for_product(db, company_id, product_id)
        if active_recipe is not None:
            return self._recipe_cost_recursive(db, company_id, active_recipe, visited)

        costing_method = (product.costing_method or "weighted_average").lower()
        if costing_method == "standard":
            return _money(Decimal(product.standard_cost or 0))

        average = db.scalar(select(func.avg(InventoryStock.average_cost)).where(InventoryStock.company_id == company_id, InventoryStock.item_id == product_id))
        if average is not None and Decimal(average) > 0:
            return _money(Decimal(average))
        latest_recorded = db.scalar(select(ProductCostHistory.cost).where(ProductCostHistory.company_id == company_id, ProductCostHistory.product_id == product_id, ProductCostHistory.effective_at <= _now()).order_by(ProductCostHistory.effective_at.desc(), ProductCostHistory.id.desc()).limit(1))
        if latest_recorded is not None:
            return _money(Decimal(latest_recorded))
        return _money(Decimal(product.standard_cost or product.purchase_price or 0))

    def _recipe_cost_recursive(self, db: Session, company_id: int, recipe: Recipe, visited: set[int]) -> Decimal:
        total = Decimal("0")
        for line in recipe.lines:
            ingredient_cost = self.ingredient_unit_cost(db, company_id, line.ingredient_product_id, visited)
            total += Decimal(line.quantity) * (Decimal("1") + Decimal(line.waste_percentage or 0) / 100) * ingredient_cost
        return _money((total * (Decimal("1") + Decimal(recipe.waste_percentage or 0) / 100)) / Decimal(recipe.yield_quantity))

    def recipe_cost(self, db: Session, company_id: int, recipe_id: int) -> Decimal:
        recipe = self.get_recipe(db, company_id, recipe_id)
        return self._recipe_cost_recursive(db, company_id, recipe, {recipe.product_id})

    def create_menu(self, db: Session, payload):
        self._company(db, payload.company_id)
        if payload.branch_id and db.scalar(select(Branch).where(Branch.id == payload.branch_id, Branch.company_id == payload.company_id, Branch.is_active.is_(True))) is None:
            raise ValueError("Branch does not belong to this company")
        menu = Menu(**payload.model_dump())
        db.add(menu)
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            raise ValueError("Menu code already exists for this company") from exc
        db.refresh(menu)
        return self.get_menu(db, payload.company_id, menu.id)

    def list_menus(self, db: Session, company_id: int):
        self._company(db, company_id)
        return list(db.scalars(select(Menu).options(selectinload(Menu.items)).where(Menu.company_id == company_id).order_by(Menu.name_ar)).all())

    def get_menu(self, db: Session, company_id: int, menu_id: int):
        menu = db.scalar(select(Menu).options(selectinload(Menu.items)).where(Menu.id == menu_id, Menu.company_id == company_id))
        if menu is None:
            raise ValueError("Menu not found")
        return menu

    def add_menu_item(self, db: Session, company_id: int, menu_id: int, payload):
        menu = self.get_menu(db, company_id, menu_id)
        self._product(db, company_id, payload.product_id)
        if payload.price_list_id and db.scalar(select(ProductPriceList).where(ProductPriceList.id == payload.price_list_id, ProductPriceList.company_id == company_id, ProductPriceList.is_active.is_(True))) is None:
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

    def pricing_analysis(self, db: Session, company_id: int, product_id: int, target_margin: Decimal = Decimal("30"), price_list_id: int | None = None):
        product = self._product(db, company_id, product_id)
        current_cost = self.ingredient_unit_cost(db, company_id, product_id)
        recipe = self._active_recipe_for_product(db, company_id, product_id)
        recipe_cost = self.recipe_cost(db, company_id, recipe.id) if recipe else None
        if recipe_cost is not None:
            current_cost = recipe_cost
        selected_price_list_id = price_list_id
        if selected_price_list_id is None:
            default_list = db.scalar(select(ProductPriceList).where(ProductPriceList.company_id == company_id, ProductPriceList.is_default.is_(True), ProductPriceList.is_active.is_(True)))
            selected_price_list_id = default_list.id if default_list else None
        else:
            if db.scalar(select(ProductPriceList.id).where(ProductPriceList.id == selected_price_list_id, ProductPriceList.company_id == company_id, ProductPriceList.is_active.is_(True))) is None:
                raise ValueError("Price list does not belong to this company")
        now = _now()
        price_query = select(ProductPrice).where(ProductPrice.company_id == company_id, ProductPrice.product_id == product_id, ProductPrice.is_active.is_(True), ProductPrice.valid_from <= now, ((ProductPrice.valid_to.is_(None)) | (ProductPrice.valid_to > now)))
        if selected_price_list_id is not None:
            price_query = price_query.where(ProductPrice.price_list_id == selected_price_list_id)
        price = db.scalar(price_query.order_by(ProductPrice.min_quantity.asc(), ProductPrice.valid_from.desc()))
        sale_price = _money(price.sale_price if price else product.sales_price)
        margin = _money(sale_price - current_cost)
        margin_pct = _money((margin / sale_price * 100) if sale_price > 0 else 0)
        recommended = _money(current_cost / (Decimal("1") - target_margin / 100)) if target_margin < 100 else None
        prices_query = select(ProductPrice).where(ProductPrice.company_id == company_id, ProductPrice.product_id == product_id)
        if selected_price_list_id is not None:
            prices_query = prices_query.where(ProductPrice.price_list_id == selected_price_list_id)
        prices = list(db.scalars(prices_query.order_by(ProductPrice.valid_from.desc()).limit(50)).all())
        costs = list(db.scalars(select(ProductCostHistory).where(ProductCostHistory.company_id == company_id, ProductCostHistory.product_id == product_id).order_by(ProductCostHistory.effective_at.desc()).limit(50)).all())
        return {"product_id": product.id, "product_name": product.name_en or product.name_ar, "price_list_id": selected_price_list_id, "current_cost": current_cost, "sale_price": sale_price, "gross_margin": margin, "gross_margin_percentage": margin_pct, "recommended_price_at_margin": recommended, "recipe_cost": recipe_cost, "price_history": [{"id": p.id, "sale_price": p.sale_price, "valid_from": p.valid_from, "valid_to": p.valid_to, "min_quantity": p.min_quantity, "source": p.source} for p in prices], "cost_history": [{"id": c.id, "cost": c.cost, "cost_type": c.cost_type, "effective_at": c.effective_at, "source": c.source} for c in costs]}

    def pricing_impact(self, db: Session, company_id: int, target_margin: Decimal = Decimal("30"), price_list_id: int | None = None, below_margin: Decimal | None = None):
        self._company(db, company_id)
        threshold = target_margin if below_margin is None else below_margin
        menus = list(db.scalars(select(Menu).options(selectinload(Menu.items)).where(Menu.company_id == company_id, Menu.is_active.is_(True))).all())
        seen: set[int] = set()
        impacted = []
        for menu in menus:
            for item in menu.items:
                if not item.is_available or item.product_id in seen:
                    continue
                seen.add(item.product_id)
                analysis = self.pricing_analysis(db, company_id, item.product_id, target_margin, price_list_id or item.price_list_id)
                if analysis["gross_margin_percentage"] < threshold:
                    impacted.append({"menu_id": menu.id, "menu_code": menu.code, "product_id": analysis["product_id"], "product_name": analysis["product_name"], "price_list_id": analysis["price_list_id"], "current_cost": analysis["current_cost"], "sale_price": analysis["sale_price"], "gross_margin_percentage": analysis["gross_margin_percentage"], "recommended_price_at_margin": analysis["recommended_price_at_margin"]})
        impacted.sort(key=lambda row: (row["gross_margin_percentage"], row["product_id"]))
        return {"target_margin": target_margin, "below_margin": threshold, "price_list_id": price_list_id, "count": len(impacted), "items": impacted}


catalog_service = CatalogService()
