import json
import urllib.request

url = "http://127.0.0.1:8001/api/v1/openapi.json"
data = json.load(urllib.request.urlopen(url, timeout=15))

terms = (
    "tenant", "company", "module", "setting",
    "onboard", "organization", "subscription"
)

print("=== RELEVANT API ROUTES ===")
for path, operations in sorted(data["paths"].items()):
    if any(term in path.lower() for term in terms):
        for method, operation in operations.items():
            if method.lower() in ("get", "post", "put", "patch", "delete"):
                print(
                    method.upper(),
                    path,
                    "|",
                    operation.get("summary", "")
                )

print("\n=== REQUEST SCHEMAS ===")
schemas = data.get("components", {}).get("schemas", {})
for name, schema in sorted(schemas.items()):
    if any(term in name.lower() for term in (
        "tenant", "company", "onboard", "organization"
    )):
        print(
            name,
            "| fields:", list(schema.get("properties", {}).keys()),
            "| required:", schema.get("required", [])
        )
