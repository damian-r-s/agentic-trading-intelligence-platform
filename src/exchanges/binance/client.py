import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import urlencode

import requests

from src.core.config import BinanceSettings


class BinanceClientError(Exception):
    pass


class BinanceConfigurationError(BinanceClientError):
    pass


class BinanceNetworkError(BinanceClientError):
    pass


class BinanceTimeoutError(BinanceNetworkError):
    pass


class BinanceResponseError(BinanceClientError):
    def __init__(self, status_code: int, payload: Any, message: str):
        self.status_code = status_code
        self.payload = payload
        super().__init__(message)


class BinanceAPIError(BinanceClientError):
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self.payload = payload
        message = extract_error_message(payload)
        super().__init__(f"Binance API error {status_code}: {message}")


class BinanceAuthenticationError(BinanceAPIError):
    pass


class BinanceRateLimitError(BinanceAPIError):
    pass


class BinanceClient:
    def __init__(self, settings: BinanceSettings):
        if not settings.is_configured:
            raise BinanceConfigurationError(
                "BINANCE_API_KEY and BINANCE_API_SECRET must be configured"
            )

        self.settings = settings

    def get_my_trades(self, symbol: str) -> list[dict[str, Any]]:
        return self._signed_get("/api/v3/myTrades", {"symbol": symbol})

    def get_deposit_history(self) -> list[dict[str, Any]]:
        return self._signed_get("/sapi/v1/capital/deposit/hisrec")

    def get_withdraw_history(self) -> list[dict[str, Any]]:
        return self._signed_get("/sapi/v1/capital/withdraw/history")

    def get_account_info(self) -> dict[str, Any]:
        return self._signed_get("/api/v3/account")

    def get_trade_fee(self, symbol: str | None = None) -> list[dict[str, Any]]:
        params = {"symbol": symbol} if symbol else None

        return self._signed_get("/sapi/v1/asset/tradeFee", params)

    def get_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        params = {"symbol": symbol} if symbol else None

        return self._signed_get("/api/v3/openOrders", params)

    def get_exchange_info(self) -> dict[str, Any]:
        return self._public_get("/api/v3/exchangeInfo")

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> list[Any]:
        return self._public_get("/api/v3/klines", {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        })

    def get_order_book(self, symbol: str, limit: int = 100) -> dict[str, Any]:
        return self._public_get("/api/v3/depth", {
            "symbol": symbol,
            "limit": limit,
        })

    def get_24h_ticker(self, symbol: str | None = None) -> Any:
        params = {"symbol": symbol} if symbol else None
        return self._public_get("/api/v3/ticker/24hr", params)

    def get_ticker_prices(self, symbols: list[str] | None = None) -> list[dict[str, Any]]:
        params = {"symbols": json.dumps(symbols)} if symbols else None
        return self._public_get("/api/v3/ticker/price", params)

    def _public_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = requests.get(
                f"{self.settings.base_url}{path}",
                params=params,
                timeout=10,
            )
        except requests.Timeout as exc:
            raise BinanceTimeoutError("Binance request timed out") from exc
        except requests.ConnectionError as exc:
            raise BinanceNetworkError(f"Binance connection error: {exc}") from exc
        except requests.RequestException as exc:
            raise BinanceNetworkError(f"Binance request error: {exc}") from exc

        payload = parse_response_payload(response)

        if response.status_code >= 400:
            raise_api_error(response.status_code, payload)

        return payload

    def _signed_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        signed_params = {
            **(params or {}),
            "recvWindow": self.settings.recv_window,
            "timestamp": self._timestamp_ms(),
        }
        signed_params["signature"] = self._sign(signed_params)

        try:
            response = requests.get(
                f"{self.settings.base_url}{path}",
                headers={"X-MBX-APIKEY": self.settings.api_key},
                params=signed_params,
                timeout=10,
            )
        except requests.Timeout as exc:
            raise BinanceTimeoutError("Binance request timed out") from exc
        except requests.ConnectionError as exc:
            raise BinanceNetworkError(f"Binance connection error: {exc}") from exc
        except requests.RequestException as exc:
            raise BinanceNetworkError(f"Binance request error: {exc}") from exc

        payload = parse_response_payload(response)

        if response.status_code >= 400:
            raise_api_error(response.status_code, payload)

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


def parse_response_payload(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError as exc:
        if response.status_code >= 400:
            return response.text

        raise BinanceResponseError(
            response.status_code,
            response.text,
            "Binance returned a non-JSON response",
        ) from exc


def raise_api_error(status_code: int, payload: Any) -> None:
    if status_code in {401, 403}:
        raise BinanceAuthenticationError(status_code, payload)

    if status_code in {418, 429}:
        raise BinanceRateLimitError(status_code, payload)

    raise BinanceAPIError(status_code, payload)


def extract_error_message(payload: Any) -> str:
    if isinstance(payload, dict):
        code = payload.get("code")
        message = payload.get("msg") or payload.get("message") or payload

        if code is not None:
            return f"{code}: {message}"

        return str(message)

    return str(payload)
