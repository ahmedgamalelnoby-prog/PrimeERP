import json
import urllib.request

d = json.load(urllib.request.urlopen(
    "http://127.0.0.1:8001/api/v1/openapi.json",
    timeout=15
))

for path, ops in sorted(d["paths"].items()):
    if any(x in path.lower() for x in ("register", "registration", "tenants")):
        for method, op in ops.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            print(f"\n{method.upper()} {path} — {op.get('summary', '')}")
            for param in op.get("parameters", []):
                print("PARAM:", param.get("name"), param.get("in"))
            for code, response in op.get("responses", {}).items():
                if code == "422":
                    continue
            body = op.get("requestBody", {}).get("content", {})
            for content_type, details in body.items():
                schema = details.get("schema", {})
                print("BODY:", content_type, json.dumps(schema, ensure_ascii=False))
