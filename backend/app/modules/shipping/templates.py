"""Built-in provider templates used as starting configurations, not as immutable facts.
Commercial terms must always be confirmed against the provider contract/current tariff.
"""
PROVIDER_TEMPLATES = [
    {"code":"ARAMEX","name":"Aramex","country_code":"EG","payment_methods":["cash","card","invoice"],"cod":True,"settlement":"contractual","services":["domestic","international","cod"]},
    {"code":"SHIPBLU","name":"ShipBlu","country_code":"EG","payment_methods":["cod","invoice","instant_payout"],"cod":True,"settlement":"instant_or_contractual","services":["domestic","cod","returns"]},
    {"code":"BOSTA","name":"Bosta","country_code":"EG","payment_methods":["cod","invoice"],"cod":True,"settlement":"contractual","services":["domestic","cod","returns"]},
    {"code":"MYLERZ","name":"Mylerz","country_code":"EG","payment_methods":["cod","invoice"],"cod":True,"settlement":"contractual","services":["domestic","cod","returns"]},
    {"code":"DHL","name":"DHL","country_code":"EG","payment_methods":["prepaid","invoice","card"],"cod":False,"settlement":"invoice","services":["express","international"]},
    {"code":"FEDEX","name":"FedEx","country_code":"EG","payment_methods":["prepaid","invoice","card"],"cod":False,"settlement":"invoice","services":["express","international"]},
    {"code":"SMSA","name":"SMSA Express","country_code":"SA","payment_methods":["cod","invoice"],"cod":True,"settlement":"contractual","services":["domestic","international","cod"]},
    {"code":"JNT","name":"J&T Express","country_code":"SA","payment_methods":["cod","invoice"],"cod":True,"settlement":"contractual","services":["domestic","cod","returns"]},
    {"code":"AYMakan","name":"iMile / AyMakan compatible template","country_code":"SA","payment_methods":["cod","invoice"],"cod":True,"settlement":"contractual","services":["domestic","cod","returns"]},
]
