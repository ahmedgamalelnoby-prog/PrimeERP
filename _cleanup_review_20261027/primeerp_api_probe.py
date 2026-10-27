import urllib.request
import urllib.error

base = "http://127.0.0.1:8001"
paths = [
    "/openapi.json",
    "/api/v1/openapi.json",
    "/docs",
    "/api/v1/docs",
    "/health",
    "/ready",
]

for path in paths:
    try:
        req = urllib.request.Request(base + path)
        with urllib.request.urlopen(req, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read(250).decode("utf-8", errors="replace")
            print(f"{response.status} {path} | {content_type}")
            if "openapi" in path:
                print(body)
    except urllib.error.HTTPError as error:
        print(f"{error.code} {path}")
    except Exception as error:
        print(f"ERROR {path}: {type(error).__name__}: {error}")
