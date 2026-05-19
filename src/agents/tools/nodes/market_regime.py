from typing import Any

from src.agents.tools.indicators import atr, sma
from src.agents.tools.state import TradingDecisionState
from src.exchanges.binance.market_data import create_binance_market_data_service


def market_regime_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol = state["symbol"]
    service = create_binance_market_data_service()
    candles = service.get_klines(symbol=symbol, interval="1d", limit=250)

    if len(candles) < 200:
        raise ValueError("At least 200 candles are required!")
    
    state["market_regime"] = compute_market_regime(candles)
    return state


def compute_market_regime(candles: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [c["close"] for c in candles]
    highs  = [c["high"]  for c in candles]
    lows   = [c["low"]   for c in candles]

    sma50  = sma(closes, 50)
    sma200 = sma(closes, 200)
    atr14  = atr(highs, lows, closes, 14)

    price = float(closes[-1])
    s50   = float(sma50[-1])
    s200  = float(sma200[-1])
    a14   = float(atr14[-1])

    if price > s50 and price > s200:
        regime = "bull"
    elif price < s50 and price < s200:
        regime = "bear"
    else:
        regime = "sideways"

    gap_pct = abs(price - s50) / s50 * 100
    if gap_pct > 10:
        trend_strength = "strong"
    elif gap_pct > 3:
        trend_strength = "moderate"
    else:
        trend_strength = "weak"

    prev_s50  = float(sma50[-2])
    prev_s200 = float(sma200[-2])
    if prev_s50 < prev_s200 and s50 > s200:
        sma_cross = "golden"
    elif prev_s50 > prev_s200 and s50 < s200:
        sma_cross = "death"
    else:
        sma_cross = "none"

    atr_pct = round(a14 / price * 100, 2)
    
    if atr_pct > 5:
        volatility = "high"
    elif atr_pct < 2:
        volatility = "low"
    else:
        volatility = "normal"

    return {
        "regime":          regime,
        "trend_strength":  trend_strength,
        "sma_cross":       sma_cross,
        "price_vs_sma50":  "above" if price > s50  else "below",
        "price_vs_sma200": "above" if price > s200 else "below",
        "atr_pct":         atr_pct,
        "volatility":      volatility,
    }