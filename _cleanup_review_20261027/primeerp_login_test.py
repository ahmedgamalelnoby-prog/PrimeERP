import json
import urllib.request
import urllib.error
import getpass

base = "http://127.0.0.1:8001"
login = input("Login (admin): ").strip()
password = getpass.getpass("Admin password: ")

def call(path, token=None, payload=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", errors="replace")
            try:
                result = json.loads(body)
            except Exception:
                result = body[:500]
            return r.status, result
    except urllib.error.HTTPError as e:
        return e.code, e.read(1000).decode("utf-8", errors="replace")
    except Exception as e:
        return None, type(e).__name__ + ": " + str(e)

status, result = call("/api/v1/identity/login", payload={
    "login": login,
    "password": password
})
password = None
print("\nLOGIN:", status)

if status == 200 and isinstance(result, dict) and result.get("access_token"):
    token = result["access_token"]
    for path in [
        "/api/v1/identity/me",
        "/api/v1/modules",
        "/api/v1/companies?active_only=true"
    ]:
        code, body = call(path, token=token)
        print("\nPATH:", path)
        print("HTTP:", code)
        if isinstance(body, dict):
            print("Response keys:", list(body.keys()))
            safe = dict(body)
            for key in list(safe):
                if any(x in key.lower() for x in ("token", "password", "secret")):
                    safe[key] = "[REDACTED]"
            print(json.dumps(safe, ensure_ascii=False)[:1200])
        else:
            print(str(body)[:1000])
    token = None
else:
    print("Login response:", str(result)[:1000])
