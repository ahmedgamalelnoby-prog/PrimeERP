"""Shipping connector contracts and provider registry."""
from dataclasses import dataclass
from typing import Any, Protocol
import os
import requests

@dataclass(frozen=True)
class ConnectorManifest:
    code: str
    name: str
    auth: str
    capabilities: tuple[str, ...]
    docs: str

class ShippingConnector(Protocol):
    manifest: ConnectorManifest
    def health(self) -> dict[str, Any]: ...
    def create_shipment(self, payload: dict[str, Any]) -> dict[str, Any]: ...
    def track(self, tracking_number: str) -> dict[str, Any]: ...
    def cancel(self, external_id: str) -> dict[str, Any]: ...
    def calculate_rate(self, payload: dict[str, Any]) -> dict[str, Any]: ...

class HttpShippingConnector:
    manifest = ConnectorManifest("GENERIC", "Generic REST courier", "api_key", ("create", "track", "cancel", "rate"), "")
    def __init__(self, base_url: str, secret_ref: str | None = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.secret_ref = secret_ref
        self.timeout = timeout
    def _headers(self):
        if not self.secret_ref:
            return {"Content-Type": "application/json"}
        value = os.getenv(self.secret_ref)
        if not value:
            raise RuntimeError(f"Shipping secret reference is not configured: {self.secret_ref}")
        return {"Authorization": value, "Content-Type": "application/json"}
    def _request(self, method, path, **kwargs):
        r = requests.request(method, f"{self.base_url}/{path.lstrip('/')}", headers=self._headers(), timeout=self.timeout, **kwargs)
        r.raise_for_status()
        return r.json() if r.content else {"success": True}
    def health(self):
        return {"provider": self.manifest.code, "configured": bool(self.base_url), "auth_ref": bool(self.secret_ref)}
    def create_shipment(self, payload): return self._request("POST", "/shipments", json=payload)
    def track(self, tracking_number): return self._request("GET", f"/shipments/{tracking_number}/tracking")
    def cancel(self, external_id): return self._request("POST", f"/shipments/{external_id}/cancel")
    def calculate_rate(self, payload): return self._request("POST", "/rates", json=payload)

PROVIDER_MANIFESTS = {
    "ARAMEX": ConnectorManifest("ARAMEX", "Aramex", "account_credentials", ("create", "label", "pickup", "track", "rate", "locations"), "https://www.aramex.com/eg/ar/developers-solution-center/aramex.com-platform"),
    "BOSTA": ConnectorManifest("BOSTA", "Bosta", "api_key", ("create", "bulk_create", "pickup", "track", "label", "webhook", "returns"), "https://docs.bosta.co/"),
    "SHIPBLU": ConnectorManifest("SHIPBLU", "ShipBlu", "api_key", ("create", "returns", "exchange", "track", "webhook", "label", "payouts"), "https://support.shipblu.com/en/support/solutions/folders/154000747134"),
    "MYLERZ": ConnectorManifest("MYLERZ", "Mylerz", "account_credentials", ("create", "track", "returns", "pickup"), "https://test.egypt.mobile.mylerz.com/Help"),
    "DHL": ConnectorManifest("DHL", "DHL", "api_key_or_oauth", ("create", "label", "pickup", "track", "rate"), "https://developer.dhl.com/"),
    "FEDEX": ConnectorManifest("FEDEX", "FedEx", "oauth", ("create", "label", "pickup", "track", "rate"), "https://developer.fedex.com/"),
    "SMSA": ConnectorManifest("SMSA", "SMSA Express", "api_key_or_account", ("create", "label", "track", "pickup"), "https://www.smsaexpress.com/"),
    "JNT": ConnectorManifest("JNT", "J&T Express", "account_credentials", ("create", "track", "label", "pickup"), "https://www.jtexpress.com/"),
}

def manifest_for(code: str) -> ConnectorManifest:
    return PROVIDER_MANIFESTS.get(code.upper(), ConnectorManifest(code.upper(), code, "configurable", ("create", "track", "cancel", "rate"), ""))
