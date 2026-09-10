"""Bosta REST connector using the documented API-key Authorization header."""
from typing import Any
import os
import requests

class BostaConnector:
    code = "BOSTA"
    default_base_url = "https://app.bosta.co/api/v2"
    def __init__(self, api_key_ref: str, base_url: str | None = None, timeout: int = 30):
        self.api_key_ref = api_key_ref
        self.base_url = (base_url or self.default_base_url).rstrip("/")
        self.timeout = timeout
    def _headers(self):
        key = os.getenv(self.api_key_ref)
        if not key:
            raise RuntimeError(f"Bosta API key reference is not configured: {self.api_key_ref}")
        return {"Authorization": key, "Content-Type": "application/json"}
    def _call(self, method: str, path: str, **kwargs: Any):
        r = requests.request(method, f"{self.base_url}/{path.lstrip('/')}", headers=self._headers(), timeout=self.timeout, **kwargs)
        r.raise_for_status()
        return r.json() if r.content else {}
    def create_delivery(self, payload: dict[str, Any]):
        return self._call("POST", "deliveries?apiVersion=1", json=payload)
    def create_bulk(self, payload: dict[str, Any]):
        return self._call("POST", "deliveries/bulk?apiVersion=1", json=payload)
    def health(self):
        return {"provider": self.code, "configured": bool(os.getenv(self.api_key_ref))}
