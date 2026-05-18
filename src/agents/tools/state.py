from typing import Any, TypedDict


class TradingDecisionState(TypedDict, total=False):
    # Input
    symbol: str

    # portfolio_snapshot_node — must run first, all parallel nodes depend on its data
    portfolio: dict[str, Any]

    # Parallel nodes (fan-out) — each fills its own field independently
    risk_metrics: dict[str, Any]        # positions, concentration, locked funds, P&L
    technical_analysis: dict[str, Any]  # EMA, RSI, MACD, Bollinger, ATR, OBV
    market_regime: dict[str, Any]       # bull/bear/sideways, trend strength, risk-on/off
    momentum: dict[str, Any]            # price acceleration, volume spikes, breakouts
    liquidity: dict[str, Any]           # order book, spread, depth, slippage estimate
    
    # analysis_node — fan-in, aggregates results from all parallel nodes
    analysis: dict[str, Any]
    recommendations: list[str]