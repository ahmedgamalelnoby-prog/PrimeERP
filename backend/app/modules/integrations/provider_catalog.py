"""Supported external platform catalog.

The catalog is deliberately metadata-only: credentials and provider API calls are
owned by IntegrationConnection/adapters. A provider is not considered connected
until a tenant creates and validates a connection.
"""

PROVIDERS = {
    "salla": {"name": "Salla", "category": "ecommerce", "market": ["sa", "mena"], "capabilities": ["products", "prices", "inventory", "orders", "customers", "refunds", "shipments", "webhooks"]},
    "zid": {"name": "Zid", "category": "ecommerce", "market": ["sa", "mena"], "capabilities": ["products", "prices", "inventory", "orders", "customers", "refunds", "shipments", "webhooks"]},
    "shopify": {"name": "Shopify", "category": "ecommerce", "market": ["global"], "capabilities": ["products", "variants", "prices", "inventory", "orders", "customers", "refunds", "fulfillment", "webhooks"]},
    "woocommerce": {"name": "WooCommerce", "category": "ecommerce", "market": ["global"], "capabilities": ["products", "variants", "prices", "inventory", "orders", "customers", "refunds", "shipments", "webhooks"]},
    "magento": {"name": "Adobe Commerce / Magento", "category": "ecommerce", "market": ["global"], "capabilities": ["products", "variants", "prices", "inventory", "orders", "customers", "refunds", "shipments", "webhooks"]},
    "amazon": {"name": "Amazon Seller Central", "category": "marketplace", "market": ["global"], "capabilities": ["products", "prices", "inventory", "orders", "returns", "fulfillment"]},
    "noon": {"name": "Noon", "category": "marketplace", "market": ["mena"], "capabilities": ["products", "prices", "inventory", "orders", "returns", "fulfillment"]},
    "tiktok_shop": {"name": "TikTok Shop", "category": "social_commerce", "market": ["supported_markets"], "capabilities": ["products", "prices", "inventory", "orders", "refunds", "webhooks"]},
    "meta_commerce": {"name": "Meta Commerce", "category": "social_commerce", "market": ["global"], "capabilities": ["catalog", "prices", "inventory", "orders", "webhooks"]},
    "talabat": {"name": "Talabat", "category": "food_delivery", "market": ["mena"], "capabilities": ["menu", "prices", "availability", "orders", "refunds", "webhooks"]},
    "elmenus": {"name": "Elmenus", "category": "food_delivery", "market": ["egypt"], "capabilities": ["menu", "prices", "availability", "orders"]},
    "careem": {"name": "Careem", "category": "food_delivery", "market": ["mena"], "capabilities": ["menu", "availability", "orders"]},
    "paymob": {"name": "Paymob", "category": "payments", "market": ["egypt", "mena"], "capabilities": ["payments", "refunds", "webhooks"]},
    "fawry": {"name": "Fawry", "category": "payments", "market": ["egypt"], "capabilities": ["payments", "refunds", "webhooks"]},
    "myfatoorah": {"name": "MyFatoorah", "category": "payments", "market": ["mena"], "capabilities": ["payments", "refunds", "webhooks"]},
    "hyperpay": {"name": "HyperPay", "category": "payments", "market": ["mena"], "capabilities": ["payments", "refunds", "webhooks"]},
    "tabby": {"name": "Tabby", "category": "payments", "market": ["mena"], "capabilities": ["payments", "refunds", "webhooks"]},
    "tamara": {"name": "Tamara", "category": "payments", "market": ["mena"], "capabilities": ["payments", "refunds", "webhooks"]},
    "aramex": {"name": "Aramex", "category": "shipping", "market": ["global"], "capabilities": ["rates", "labels", "tracking", "pickup", "webhooks"]},
    "dhl": {"name": "DHL", "category": "shipping", "market": ["global"], "capabilities": ["rates", "labels", "tracking", "pickup", "webhooks"]},
    "fedex": {"name": "FedEx", "category": "shipping", "market": ["global"], "capabilities": ["rates", "labels", "tracking", "pickup", "webhooks"]},
    "bosta": {"name": "Bosta", "category": "shipping", "market": ["egypt"], "capabilities": ["rates", "shipment", "tracking", "cod", "webhooks"]},
    "mylerz": {"name": "Mylerz", "category": "shipping", "market": ["egypt"], "capabilities": ["rates", "shipment", "tracking", "cod", "webhooks"]},
    "shipblu": {"name": "ShipBlu", "category": "shipping", "market": ["egypt"], "capabilities": ["rates", "shipment", "tracking", "cod", "webhooks"]},
}


def list_providers(category: str | None = None):
    rows = []
    for key, value in sorted(PROVIDERS.items()):
        if category and value["category"] != category:
            continue
        rows.append({"provider": key, **value})
    return rows
