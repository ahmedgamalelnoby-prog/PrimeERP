"""Aramex REST/JSON connector helpers."""
from typing import Any
import os
import requests

class AramexConnector:
    code = "ARAMEX"
    default_base_url = "https://ws.aramex.net/shippingapi.v2/shipping/service_1_0.svc/json"
    def __init__(self, account_number_ref: str, username_ref: str, password_ref: str, account_pin_ref: str, base_url: str | None = None, timeout: int = 30):
        self.refs = {"AccountNumber": account_number_ref, "UserName": username_ref, "Password": password_ref, "AccountPin": account_pin_ref}
        self.base_url = (base_url or self.default_base_url).rstrip("/")
        self.timeout = timeout
    def _value(self, ref: str):
        value = os.getenv(ref)
        if not value:
            raise RuntimeError(f"Aramex credential reference is not configured: {ref}")
        return value
    def _client_info(self):
        return {"UserName": self._value(self.refs["UserName"]), "Password": self._value(self.refs["Password"]), "Version": "1.0", "AccountNumber": self._value(self.refs["AccountNumber"]), "AccountPin": self._value(self.refs["AccountPin"]), "AccountEntity": "EG", "Source": 24}
    def call(self, operation: str, payload: dict[str, Any]):
        body = dict(payload); body.setdefault("ClientInfo", self._client_info())
        response = requests.post(f"{self.base_url}/{operation}", json=body, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    def create_shipment(self, payload): return self.call("CreateShipments", {"Shipments": [payload]})
    def track(self, tracking_number): return self.call("TrackShipments", {"ShipmentNumber": tracking_number})
    def calculate_rate(self, payload): return self.call("CalculateRate", payload)
