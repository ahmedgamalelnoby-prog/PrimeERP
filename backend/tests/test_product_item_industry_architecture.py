from app.modules.catalog.models import CatalogProduct, Recipe
from app.modules.companies.industry_models import CompanyIndustryProfile
from app.modules.companies.industry_registry import behavior_for
from app.modules.commerce.models import PurchaseLine, SalesLine


def test_product_and_item_are_explicitly_separate_database_entities():
    assert CatalogProduct.__tablename__ == "catalog_products"
    assert CatalogProduct.__table__.c.item_id is not None
    assert CatalogProduct.__table__.c.product_kind is not None
    assert Recipe.__table__.c.catalog_product_id is not None
    assert SalesLine.__table__.c.catalog_product_id is not None
    assert PurchaseLine.__table__.c.catalog_product_id is not None


def test_industry_profile_changes_operational_behavior_not_accounting_core():
    restaurant = behavior_for("restaurant")
    cafe = behavior_for("cafe")
    perfume = behavior_for("perfume_manufacturing")
    assert restaurant.enabled("recipes")
    assert restaurant.enabled("kitchen")
    assert cafe.enabled("recipes")
    assert perfume.enabled("recipes")
    assert perfume.enabled("packaging")
    assert not perfume.enabled("kitchen")


def test_unknown_industry_is_safe_and_does_not_enable_features():
    assert not behavior_for("unknown").enabled("recipes")


def test_industry_profile_is_company_scoped():
    assert CompanyIndustryProfile.__table__.c.company_id is not None
    assert CompanyIndustryProfile.__table__.c.industry_code is not None
