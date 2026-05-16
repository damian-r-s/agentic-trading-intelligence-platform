import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from src.core.config import BinanceSettings


class BinanceClientError(Exception):
    pass


class BinanceConfigurationError(BinanceClientError):
    pass


class BinanceAPIError(BinanceClientError):
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Binance API error {status_code}: {payload}")


class BinanceClient:
    def __init__(self, settings: BinanceSettings):
        if not settings.is_configured:
            raise BinanceConfigurationError(
                "BINANCE_API_KEY and BINANCE_API_SECRET must be configured"
            )

        self.settings = settings

    def get_account_info(self) -> dict[str, Any]:
        return self._signed_get("/api/v3/account")

    def _signed_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        signed_params = {
            **(params or {}),
            "recvWindow": self.settings.recv_window,
            "timestamp": self._timestamp_ms(),
        }
        signed_params["signature"] = self._sign(signed_params)

        response = requests.get(
            f"{self.settings.base_url}{path}",
            headers={"X-MBX-APIKEY": self.settings.api_key},
            params=signed_params,
            timeout=10,
        )

        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if response.status_code >= 400:
            raise BinanceAPIError(response.status_code, payload)

        return payload

    def _sign(self, params: dict[str, Any]) -> str:
        query_string = urlencode(params)
        return hmac.new(
            self.settings.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _timestamp_ms() -> int:
        return int(time.time() * 1000)
