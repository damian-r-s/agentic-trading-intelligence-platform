from typing import Any, TypedDict


class TradingDecisionState(TypedDict, total=False):
    # Input
    symbol: str

    # portfolio_snapshot_node — must run first, all parallel nodes depend on its data
    portfolio: dict[str, Any]
    daily_candles: list[dict[str, Any]]  # 250 daily OHLCV candles, fetched once, shared by market_regime + momentum

    # Parallel nodes (fan-out) — each fills its own field independently
    risk_metrics: dict[str, Any]        # positions, concentration, locked funds, P&L
    technical_analysis: dict[str, Any]  # EMA, RSI, MACD, Bollinger, ATR, OBV
    market_regime: dict[str, Any]       # bull/bear/sideways, trend strength, risk-on/off
    momentum: dict[str, Any]            # price acceleration, volume spikes, breakouts
    liquidity: dict[str, Any]           # order book, spread, depth, slippage estimate
    correlation: dict[str, Any]         # BTC/ETH correlation, diversification score
    news_sentiment: dict[str, Any]      # headlines, FinBERT scores, sentiment signal

    # strategy_node - fan-in, aggregates all signals into a trading decision
    strategy: dict[str, Any]            # action: BUY/WAIT/AVOID, entry_zone, thesis, confidence