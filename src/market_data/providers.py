"""
Protocol interfaces for all market data providers.

Agents depend on these interfaces, not on concrete implementations.
This makes it possible to swap Binance for CoinGecko without touching agent code.

Current implementations:
  CandleProvider      → BinanceMarketDataService
  OrderBookProvider   → BinanceMarketDataService
  TickerProvider      → BinanceMarketDataService
  MarketDataProvider  → (planned: CoinGecko / CoinMarketCap)
  DerivativesProvider → (planned: Binance Futures API /fapi/v1/*)
  NewsProvider        → (planned: CryptoPanic API)
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CandleProvider(Protocol):
    """OHLCV candle data. Required by: TechnicalAnalysisAgent, MomentumAgent."""

    def get_klines(self, symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
        ...


@runtime_checkable
class OrderBookProvider(Protocol):
    """Order book depth data. Required by: LiquidityAgent."""

    def get_order_book(self, symbol: str, limit: int) -> dict[str, Any]:
        ...


@runtime_checkable
class TickerProvider(Protocol):
    """24h ticker statistics (price change, volume, high/low). Required by: MomentumAgent, MarketRegimeAgent."""

    def get_24h_stats(self, symbol: str) -> dict[str, Any]:
        ...


@runtime_checkable
class MarketDataProvider(Protocol):
    """
    Macro market data (BTC dominance, fear & greed, sector performance).
    Required by: MarketRegimeAgent, MarketSaturationAgent.

    Planned implementations: CoinGecko, CoinMarketCap, alternative.me
    """

    def get_global_market_metrics(self) -> dict[str, Any]:
        ...

    def get_btc_dominance(self) -> dict[str, Any]:
        ...

    def get_fear_greed_index(self) -> dict[str, Any]:
        ...

    def get_sector_performance(self) -> dict[str, Any]:
        ...

    def get_top_gainers_losers(self) -> dict[str, Any]:
        ...


@runtime_checkable
class DerivativesProvider(Protocol):
    """
    Derivatives market data (funding rates, open interest, long/short ratio).
    Required by: MarketSaturationAgent.

    Planned implementation: Binance Futures API (/fapi/v1/*)
    """

    def get_funding_rates(self, symbols: list[str]) -> dict[str, Any]:
        ...

    def get_open_interest(self, symbols: list[str]) -> dict[str, Any]:
        ...

    def get_long_short_ratio(self, symbols: list[str]) -> dict[str, Any]:
        ...


@runtime_checkable
class NewsProvider(Protocol):
    """
    Crypto news and sentiment data.
    Required by: NewsSentimentAgent.

    Planned implementation: CryptoPanic API, X/Twitter scraper
    """

    def get_crypto_news(self, symbol: str) -> list[dict[str, Any]]:
        ...

    def get_project_news(self, project: str) -> list[dict[str, Any]]:
        ...
