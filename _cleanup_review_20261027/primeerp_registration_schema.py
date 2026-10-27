import json
import urllib.request

url = "http://127.0.0.1:8001/api/v1/openapi.json"
d = json.load(urllib.request.urlopen(url, timeout=15))

name = "TenantRegistrationRequest"
schema = d["components"]["schemas"][name]

print("=== REGISTRATION REQUEST SCHEMA ===")
print(json.dumps(schema, indent=2, ensure_ascii=False))

print("\n=== REGISTRATION ENDPOINT ===")
op = d["paths"]["/api/v1/saas/register"]["post"]
print(json.dumps({
    "summary": op.get("summary"),
    "description": op.get("description"),
    "responses": op.get("responses"),
    "security": op.get("security")
}, indent=2, ensure_ascii=False))

print("\n=== RELATED RESPONSE SCHEMAS ===")
for name in ("TenantRegistrationResponse", "RegisteredTenantResponse",
             "RegisteredCompanyResponse"):
    if name in d["components"]["schemas"]:
        print(f"\n{name}")
        print(json.dumps(d["components"]["schemas"][name],
                         indent=2, ensure_ascii=False))
