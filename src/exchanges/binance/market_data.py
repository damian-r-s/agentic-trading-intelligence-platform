from decimal import Decimal
from typing import Any, Literal

from src.core.config import get_binance_settings
from src.exchanges.binance.client import BinanceClient

KlineInterval = Literal[
    "1m", "3m", "5m", "15m", "30m",
    "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
]


class BinanceMarketDataService:
    """Normalizes raw Binance market data into clean, named structures."""

    def __init__(self, client: BinanceClient):
        self.client = client

    def get_klines(
        self,
        symbol: str,
        interval: KlineInterval = "1h",
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        raw = self.client.get_klines(symbol, interval, limit)
        return [_normalize_kline(k) for k in raw]

    def get_order_book(self, symbol: str, limit: int = 100) -> dict[str, Any]:
        raw = self.client.get_order_book(symbol, limit)
        return _normalize_order_book(symbol, raw)

    def get_24h_stats(self, symbol: str) -> dict[str, Any]:
        raw = self.client.get_24h_ticker(symbol)
        return _normalize_24h_ticker(raw)


def _normalize_kline(kline: list[Any]) -> dict[str, Any]:
    # Binance returns a 12-element array: [open_time, open, high, low, close, volume, ...]
    return {
        "open_time": kline[0],
        "open": kline[1],
        "high": kline[2],
        "low": kline[3],
        "close": kline[4],
        "volume": kline[5],
        "close_time": kline[6],
        "quote_volume": kline[7],
        "trade_count": kline[8],
        "taker_buy_volume": kline[9],
        "taker_buy_quote_volume": kline[10],
    }


def _normalize_order_book(symbol: str, raw: dict[str, Any]) -> dict[str, Any]:
    bids = [{"price": b[0], "quantity": b[1]} for b in raw.get("bids", [])] # sorted bids, descending order
    asks = [{"price": a[0], "quantity": a[1]} for a in raw.get("asks", [])] # sorted asks, ascending order

    best_bid = Decimal(bids[0]["price"]) if bids else Decimal("0")
    best_ask = Decimal(asks[0]["price"]) if asks else Decimal("0")
    mid_price = (best_bid + best_ask) / 2
    spread = best_ask - best_bid
    spread_pct = spread / best_bid * 100 if best_bid > 0 else Decimal("0")

    bid_depth = sum(Decimal(b["quantity"]) for b in bids)
    ask_depth = sum(Decimal(a["quantity"]) for a in asks)

    def fmt(d: Decimal) -> str:
        return format(d.normalize(), "f")

    return {
        "symbol": symbol,
        "last_update_id": raw.get("lastUpdateId"),
        "bids": bids,
        "asks": asks,
        "best_bid": fmt(best_bid),
        "best_ask": fmt(best_ask),
        "spread": fmt(spread),
        "spread_pct": fmt(spread_pct),
        "mid_price": fmt(mid_price),
        "bid_depth": fmt(bid_depth),
        "ask_depth": fmt(ask_depth),
    }


def _normalize_24h_ticker(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": raw.get("symbol"),
        "price_change": raw.get("priceChange"),
        "price_change_pct": raw.get("priceChangePercent"),
        "last_price": raw.get("lastPrice"),
        "high": raw.get("highPrice"),
        "low": raw.get("lowPrice"),
        "volume": raw.get("volume"),
        "quote_volume": raw.get("quoteVolume"),
        "open_price": raw.get("openPrice"),
        "trade_count": raw.get("count"),
        "weighted_avg_price": raw.get("weightedAvgPrice"),
    }


def create_binance_market_data_service() -> BinanceMarketDataService:
    return BinanceMarketDataService(BinanceClient(get_binance_settings()))
